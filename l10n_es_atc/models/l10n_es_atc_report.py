# Copyright 2025 Tecnativa - Carlos Lopez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import contextlib
import os
import subprocess
import tempfile
import zipfile
from io import BytesIO

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import ustr
from odoo.tools.float_utils import float_is_zero, float_round

from odoo.addons.l10n_es_aeat.models.spanish_states_mapping import SPANISH_STATES

# The URL to download the file
# this should be inherited in the module that uses this model
# the key is the ATC model number
# the value is the URL to download the file
# Example:
# from odoo.addons.l10n_es_atc.models.l10n_es_atc_report import ATC_JAR_URL
# ATC_JAR_URL["420"] = "https://example.com/atc_420.zip"
ATC_JAR_URL = {}


class L10nEsAtcReport(models.AbstractModel):
    _inherit = "l10n.es.aeat.report.tax.mapping"
    _name = "l10n.es.atc.report"

    output_type = fields.Selection(
        selection=[
            ("B", "Imprimir Borrador"),
            ("I", "Imprimir autoliquidación final"),
            ("T", "Presentación telemática"),
        ],
        string="Tipo de salida",
        default="T",
    )
    payment_type = fields.Selection(
        selection=[
            ("1", "1 - Efectivo"),
            ("2", "2 - Adeudo en cuenta"),
            ("3", "3 - Pago fraccionado"),
            ("4", "4 - Domiciliación bancaria"),
            ("5", "5 - Pago telemático"),
            ("6", "6 - Aplazamiento 6 meses medidas Covid"),
        ],
        string="Forma de pago",
        compute="_compute_payment_type",
        store=True,
        readonly=False,
    )

    @api.model
    def _get_sequence_code(self):
        # override the sequence name to atc
        return f"atc{self._aeat_number}-sequence"

    @api.model
    def _prepare_aeat_sequence_vals(self, sequence, aeat_num, company):
        values = super()._prepare_aeat_sequence_vals(sequence, aeat_num, company)
        # change the sequence code for ATC
        values["code"] = "atc.sequence.type"
        return values

    def _register_hook(self, companies=None):
        # This AbstractModel must be inherited by other models
        # and must not define the _aeat_number attribute.
        # Therefore, skip this check in this case.
        if self._name != "l10n.es.atc.report":
            return super()._register_hook(companies=companies)

    @api.depends("output_type")
    def _compute_payment_type(self):
        for record in self:
            if not record.payment_type and record.output_type == "T":
                record.payment_type = "5"

    def _atc_get_messages(self):
        """
        Get the messages to display to the user in case of errors.
        :return: list of messages
        :rtype: list
        """
        messages = []
        partner_company = self.company_id.partner_id
        if not partner_company.street:
            messages.append(_("- The company %s has no street") % partner_company.name)
        if not partner_company.zip:
            messages.append(
                _("- The company %s has no zip code") % partner_company.name
            )
        return messages

    def _atc_validate_fields(self):
        """
        Validate the fields to be used in the declaration.
        """
        messages = self._atc_get_messages()
        if messages:
            raise UserError(
                _("Please fix the following errors:\n%s") % "\n".join(messages)
            )

    def _atc_get_country_state_code(self, country_state):
        codigo_provincia = SPANISH_STATES.get(country_state.code)
        if not codigo_provincia:
            raise UserError(
                _("The state code is not mapped for state: %s", country_state.code)
            )
        return codigo_provincia

    def _atc_run_cmd(self, report_name, filename, jar_filename, main_class):
        """
        Run the command to generate the report
        :param report_name: name of the report to generate
        :param filename: name of the file to generate without extension
        :param jar_filename: jar file name
        :param main_class: main class
        :return: browse_record(ir.attachment)
        """
        xml_data = self.env["ir.actions.report"]._render_qweb_xml(
            report_name, self.ids
        )[0]
        dir_paths = self._atc_make_tmp_dir(filename)
        with open(dir_paths["xml_path"], "w", encoding="iso-8859-1") as f:
            f.write(xml_data.decode("iso-8859-1"))
        full_filename = (
            f"{filename}.dec" if self.output_type == "T" else f"{filename}.pdf"
        )
        cmd = self._atc_make_cmd(dir_paths, filename, jar_filename, main_class)
        try:
            result = subprocess.run(
                " ".join(cmd), shell=True, capture_output=True, text=True
            )
            if result.returncode != 0:
                raise UserError(
                    f"Error al generar el modelo:\n"
                    f"Código de salida: {result.returncode}\n"
                    f"STDOUT:\n{result.stdout}\n"
                    f"STDERR:\n{result.stderr}"
                )
        except Exception as e:
            raise UserError(
                _(f"Excepción durante la ejecución del comando:\n{ustr(e)}")
            ) from e
        # check if there are errors
        if os.path.exists(dir_paths["errores_path"]):
            errores = ""
            with open(dir_paths["errores_path"], encoding="iso-8859-1") as f:
                errores = f.read()
            if errores:
                raise UserError(
                    _(
                        "No se pudo generar el archivo. Errores encontrados:\n %s",
                        errores,
                    )
                )
        file_content = self._atc_get_report_data(dir_paths, full_filename)
        return self._atc_save_report(file_content, full_filename)

    def _atc_make_tmp_dir(self, file_name):
        """
        Create a temporary directory to store the files
        :param file_name: name of the file to create witout extension
        :return: dict with the paths of the files
        :rtype: dict
        """
        TMP_DIR = tempfile.mkdtemp()
        xml_path = os.path.join(TMP_DIR, f"{file_name}.xml")
        errores_path = os.path.join(TMP_DIR, "FICH_ERRORES.txt")
        control_path = os.path.join(TMP_DIR, "FICH_CONTROL.txt")
        resultado_path = os.path.join(TMP_DIR, "Resultado")
        servicio_path = os.path.join(TMP_DIR, "Servicio")
        os.makedirs(resultado_path, exist_ok=True)
        os.makedirs(servicio_path, exist_ok=True)
        return {
            "xml_path": xml_path,
            "errores_path": errores_path,
            "control_path": control_path,
            "resultado_path": resultado_path,
            "servicio_path": servicio_path,
        }

    def _atc_make_cmd(self, dir_paths, filename, jar_filename, main_class):
        """
        Make the command to run the java program
        :param dir_paths: dict with the paths of the files
        :param filename: name of the file to generate without extension
        :param jar_filename: jar file name
        :param main_class: main class the jar file
        :return: list with the command to run
        """
        irc_param = self.env["ir.config_parameter"].sudo()
        java_param = irc_param.get_param("l10n_es_atc.java_parameters")
        xml_path = dir_paths["xml_path"]
        errores_path = dir_paths["errores_path"]
        control_path = dir_paths["control_path"]
        resultado_path = dir_paths["resultado_path"]
        servicio_path = dir_paths["servicio_path"]
        jar_attachment = self._get_or_download_atc_jar(jar_filename)
        jar_path = jar_attachment._full_path(jar_attachment.store_fname)
        cmd = [
            "java ",
            java_param,
            f" -cp {jar_path}",
            main_class,
            f'/E:"{xml_path}"',
            f'/R:"{errores_path}"',
            f'/F:"{control_path}"',
            f'/S:"{self.output_type}"',
            f'/T:"{resultado_path}"',
            f'/P:"{filename}"',
            '/N:"N"',
            f'/W:"{servicio_path}"',
        ]
        return cmd

    def _get_or_download_atc_jar(self, jar_filename, timeout=60):
        """
        Get the ATC jar file from the database or download it from the server
        :param timeout: max timeout for the request"""
        attachment = self.env["ir.attachment"].search(
            [("name", "=", jar_filename)], limit=1
        )
        if attachment:
            return attachment
        # If the jar file is not present, download it from the server
        url = ATC_JAR_URL.get(self._aeat_number)
        if not url:
            raise UserError(
                _(
                    "Please configure the JAR URL for %s "
                    "by inheriting the variable `ATC_JAR_URL`.",
                    self._aeat_number,
                )
            )
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
        except Exception as error:
            raise UserError(
                _(
                    "Error downloading the jar file from: %(url)s\n%(error)s",
                    url=url,
                    error=ustr(error),
                )
            ) from error
        content = response.content
        if not content:
            raise UserError(
                _("The HTTP response from %(url)s is empty (no content)", url=url)
            )
        jar_content = None
        with contextlib.suppress(zipfile.BadZipFile):
            with zipfile.ZipFile(BytesIO(content)) as zip_file:
                for file_name in zip_file.namelist():
                    if file_name.endswith(jar_filename):
                        jar_content = zip_file.read(file_name)
                        break
        if not jar_content:
            raise UserError(
                _(
                    "The jar file: %(jar_filename)s "
                    "is not present in the zip file downloaded from: %(url)s",
                    jar_filename=jar_filename,
                    url=url,
                )
            )
        # Save the jar file in the database
        return self.env["ir.attachment"].create(
            {
                "name": jar_filename,
                "raw": jar_content,
                "company_id": False,
            }
        )

    def _atc_get_report_data(self, dir_paths, file_name):
        """
        Get the report data from the file
        :param dir_paths: dict with the paths of the files
        :param file_name: name of the file to get
        :return: content of the file
        :rtype: str
        """
        resultado_path = dir_paths["resultado_path"]
        file_path = os.path.join(resultado_path, file_name)
        if self.env.context.get("test_l10n_es_atc_report") or not os.path.exists(
            file_path
        ):
            raise UserError(
                _(
                    "Declaracion no generada. Revisa si el XML es válido y "
                    "los parámetros correctos."
                )
            )
        file_content = ""
        with open(file_path, "rb") as f:
            file_content = f.read()
        return file_content

    def _atc_save_report(self, file_content, file_name):
        """
        Save the file in the database
        :param file_content: content of the file to save
        :param file_name: name of the file to save
        :return: browse_record(ir.attachment)
        """
        Attachment = self.env["ir.attachment"]
        attachment = Attachment.search(
            [
                ("name", "=", file_name),
                ("res_model", "=", self._name),
                ("res_id", "=", self.id),
            ],
            limit=1,
        )
        datas = base64.b64encode(file_content).decode("ascii")
        if attachment:
            attachment.write({"datas": datas})
        else:
            attachment = Attachment.create(
                {
                    "name": file_name,
                    "type": "binary",
                    "datas": datas,
                    "res_model": self._name,
                    "res_id": self.id,
                }
            )
        return attachment

    def _get_amount_by_fields(self, fields):
        report_data = []
        for field_base, field_amount in fields:
            line_vals = self._get_amount_by_field(field_base, field_amount)
            if float_is_zero(line_vals["base"], precision_digits=2):
                continue
            report_data.append(line_vals)
        return report_data

    def _get_amount_by_field(self, field_base, field_amount):
        """
        Get the amount by field base and field amount
        :param field_base: number of field to calculate the amount
        :param field_amount: number of field to calculate the amount
        :return: dict with base, amount and amount_by_tax
            amount_by_tax is a dict with the tax id as key
            and a dict with base, amount and percentage as value
            {
                tax_id: {
                    "base": base,
                    "amount": amount,
                    "percentage": percentage,
                }
            }
        :rtype: dict
        """
        base_tax_lines = self.tax_line_ids.filtered(
            lambda x: x.field_number == field_base
        )
        tax_lines = self.tax_line_ids.filtered(lambda x: x.field_number == field_amount)
        taxes = tax_lines.mapped("move_line_ids.tax_line_id")
        data_total = {
            "base": 0,
            "amount": 0,
            "amount_by_tax": {},
        }
        default_tax_data = {
            "base": 0,
            "amount": 0,
            "percentage": 0,
        }
        for base_tax in base_tax_lines:
            map_line = base_tax.map_line_id
            taxes = base_tax.move_line_ids.tax_ids
            for tax in taxes:
                base_aml = base_tax.move_line_ids.filtered(
                    lambda x, tax=tax: tax in x.tax_ids
                )
                base = map_line._get_amount_from_moves(base_aml)
                data_total["base"] += base
                data_total["amount_by_tax"].setdefault(tax, dict(default_tax_data))
                data_total["amount_by_tax"][tax]["base"] += self._format_amount(base)
        for tax_line in tax_lines:
            map_line = tax_line.map_line_id
            taxes = tax_line.move_line_ids.tax_line_id
            for tax in taxes:
                tax_aml = tax_line.move_line_ids.filtered(
                    lambda x, tax=tax: x.tax_line_id == tax
                )
                amount = map_line._get_amount_from_moves(tax_aml)
                data_total["amount"] += amount
                data_total["amount_by_tax"].setdefault(tax, dict(default_tax_data))
                data_total["amount_by_tax"][tax]["amount"] += self._format_amount(
                    amount
                )
                data_total["amount_by_tax"][tax]["percentage"] = self._format_amount(
                    tax.amount
                )
        # format amount
        data_total.update(
            {
                "base": self._format_amount(data_total["base"]),
                "amount": self._format_amount(data_total["amount"]),
            }
        )
        return data_total

    def _format_amount(self, amount):
        """
        Format amount to 2 decimal places and convert to int
        Example: 1234.56 -> 123456
        """
        return int(float_round(amount * 100, 2))
