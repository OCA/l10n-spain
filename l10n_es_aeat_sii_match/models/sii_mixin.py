# Copyright 2018 Studio73 - Abraham Anes
# Copyright 2019 Studio73 - Pablo Fuentes
# Copyright 2022,2026 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from deepdiff import DeepDiff
from zeep.helpers import serialize_object

from odoo import Command, api, fields, models
from odoo.modules.registry import Registry
from odoo.tools import float_compare


class SiiMixin(models.AbstractModel):
    _inherit = "sii.mixin"

    sii_match_sent = fields.Text(string="SII match sent", copy=False, readonly=True)
    sii_match_return = fields.Text(string="SII match return", copy=False, readonly=True)
    sii_match_state = fields.Selection(
        string="Match state",
        readonly=True,
        copy=False,
        selection=[
            ("1", "No testable"),
            ("2", "In process of contrast"),
            ("3", "Not contrasted"),
            ("4", "Partially contrasted"),
            ("5", "Contrasted"),
        ],
        help="- No testable: The counterpart is not subscribed to SII "
        "the record will not be contrasted.\n"
        "- In process of contrast: AEAT is processing the data "
        "soon will be a result.\n"
        "- Not contrasted: The counterpart "
        "has not sent the invoice to SII, "
        "AEAT gives up to 4 months in order "
        "to contrast the information.\n"
        "- Partially contrasted: A invoice has been found "
        "but some data is different.\n"
        "- Contrasted: The counterpart has send "
        "the invoice to SII, all is OK.",
    )
    sii_contrast_state = fields.Selection(
        string="AEAT contrast state",
        readonly=True,
        copy=False,
        selection=[
            ("correct", "Correct"),
            ("no_exist", "Doesn't exist"),
            ("partially", "Partially correct"),
        ],
    )
    sii_match_difference_ids = fields.One2many(
        string="SII match differences",
        readonly=True,
        copy=False,
        comodel_name="l10n.es.aeat.sii.match.difference",
        inverse_name="invoice_id",
        domain=lambda self: [("model", "=", self._name)],
    )

    def _get_diffs(self, odoo_values, sii_values):
        sii_values = json.loads(json.dumps(serialize_object(sii_values)))
        dp = self.env["decimal.precision"].precision_get("Account")
        res = []
        diff = DeepDiff(odoo_values, sii_values)
        differences = diff.get("type_changes", {})
        differences.update(diff.get("values_changed", {}))
        for label, value in list(differences.items()):
            sii_value = value["new_value"]
            odoo_value = value["old_value"]
            label = label.split("['")[-1].replace("']", "")
            if sii_value is not None:
                different = sii_value != odoo_value
                # We made an explicit case for TipoImpositivo because we get
                # always 2 numbers as strings, one with decimal point separator
                # and another without
                if label == "TipoImpositivo":
                    odoo_value = float(odoo_value)
                if isinstance(odoo_value, float | int):
                    sii_value = float(sii_value)
                    different = (
                        float_compare(odoo_value, sii_value, precision_digits=dp) != 0
                    )
                elif isinstance(odoo_value, str):
                    sii_value = sii_value.strip()
                    odoo_value = odoo_value.strip()
                    different = sii_value != odoo_value
                if different:
                    res.append(
                        {
                            "sii_field": label,
                            "sii_return_field_value": sii_value,
                            "sii_sent_field_value": odoo_value,
                        }
                    )
        return res

    def _get_diffs_values(self, sii_values):
        self.ensure_one()
        res = []
        if self.aeat_content_sent:
            odoo_values = json.loads(self.aeat_content_sent)
            mapping_key = self._get_mapping_key()
            if mapping_key in ["out_invoice", "out_refund"]:
                res += self._get_diffs(
                    odoo_values["FacturaExpedida"], sii_values["DatosFacturaEmitida"]
                )
            elif mapping_key in ["in_invoice", "in_refund"]:
                res += self._get_diffs(
                    odoo_values["FacturaRecibida"], sii_values["DatosFacturaRecibida"]
                )
        return res

    def _get_match_report_values(self, inv_dict):
        """Obtain from the AEAT returned dictionary, the matching result values with the
        current Odoo document represented by `self`. This dictionary can be used for
        writing values, dropping some keys, into `l10n.es.aeat.sii.match.result` or
        into `sii.mixin` documents.
        """
        if not inv_dict:
            inv_dict = {}
            # As we don't have .get method in zeep results, we have to go this way
            name = False
            csv = False
            match_state = False
        else:
            name = inv_dict["IDFactura"]["NumSerieFacturaEmisor"]
            csv = inv_dict["DatosPresentacion"]["CSV"]
            match_state = (
                inv_dict["EstadoFactura"]["EstadoCuadre"]
                if inv_dict["EstadoFactura"]
                else False
            )
        if match_state:
            inv_location = "both"
            contrast_state = "correct"
        elif self:
            inv_location = "odoo"
            contrast_state = "no_exist"
        elif inv_dict:
            inv_location = "sii"
            contrast_state = "no_exist"
        diffs = self._get_diffs_values(inv_dict) if (inv_dict and self) else []
        if diffs:
            contrast_state = "partially"
            for diff in diffs:  # Fill the document o2m values
                diff["invoice_id"] = self.id
                diff["model"] = self._name if self else False
        vals = {
            "invoice": name,
            "invoice_id": self.id,
            "model": self._name if self else False,
            "csv": csv,
            "invoice_location": inv_location,
            "sii_contrast_state": contrast_state,
            "sii_match_state": match_state,
            "sii_match_difference_ids": [Command.create(x) for x in diffs],
        }
        if inv_dict:
            vals["sii_match_return"] = json.dumps(str(inv_dict), indent=4)
        return vals

    def contrast_aeat(self):
        """Overridable hook for raising any error or filtering out records if needed."""
        for document in self:
            document._contrast_invoice_to_aeat()

    def _get_contrast_invoice_dict_out(self):
        """Build dict with data to send to AEAT WS for invoice types:
        out_invoice and out_refund.
        :return: invoices (dict) : Dict XML with data for this invoice.
        """
        self.ensure_one()
        invoice_date = self._change_date_format(self._get_document_date())
        partner = self._aeat_get_partner()
        company = self.company_id
        ejercicio = self._get_document_fiscal_year()
        periodo = self._get_document_period()
        number = self._get_document_serial_number()
        inv_dict = {
            "FiltroConsulta": {},
            "PeriodoLiquidacion": {"Ejercicio": ejercicio, "Periodo": periodo},
            "IDFactura": {
                "IDEmisorFactura": {
                    "NIF": company.partner_id._parse_aeat_vat_info()[2]
                },
                "NumSerieFacturaEmisor": (number or "")[:60],
                "FechaExpedicionFacturaEmisor": invoice_date,
            },
        }
        if not self._is_aeat_simplified_invoice():
            # Simplified invoices don't have counterpart
            inv_dict["Contraparte"] = {"NombreRazon": partner.name[0:120]}
            # Uso condicional de IDOtro/NIF
            inv_dict["Contraparte"].update(self._get_sii_identifier())
        return inv_dict

    def _get_contrast_invoice_dict_in(self):
        """Build dict with data to send to AEAT WS for invoice types:
        in_invoice and in_refund.
        :return: invoices (dict) : Dict XML with data for this invoice.
        """
        self.ensure_one()
        invoice_date = self._change_date_format(self._get_document_date())
        ejercicio = self._get_document_fiscal_year()
        periodo = self._get_document_period()
        inv_dict = {
            "FiltroConsulta": {},
            "IDFactura": {
                "IDEmisorFactura": {
                    "NombreRazon": self._aeat_get_partner().name[0:120],
                },
                "NumSerieFacturaEmisor": ((self.ref or "")[:60]),
                "FechaExpedicionFacturaEmisor": invoice_date,
            },
            "PeriodoLiquidacion": {"Ejercicio": ejercicio, "Periodo": periodo},
        }
        # Uso condicional de IDOtro/NIF
        ident = self._get_sii_identifier()
        inv_dict["IDFactura"]["IDEmisorFactura"].update(ident)
        return inv_dict

    def _get_contrast_invoice_dict(self):
        self.ensure_one()
        self._aeat_check_exceptions()
        mapping_key = self._get_mapping_key()
        if mapping_key in ["out_invoice", "out_refund"]:
            return self._get_contrast_invoice_dict_out()
        elif mapping_key in ["in_invoice", "in_refund"]:
            return self._get_contrast_invoice_dict_in()
        return {}

    def _contrast_invoice_to_aeat(self):
        for document in self:
            mapping_key = document._get_mapping_key()
            serv = document._connect_aeat(mapping_key)
            header = document._get_aeat_header(False, True)
            inv_dict = document._get_contrast_invoice_dict()
            inv_vals = {"sii_match_sent": json.dumps(inv_dict, indent=4)}
            try:
                res_line = False
                if mapping_key in ["out_invoice", "out_refund"]:
                    res = serv.ConsultaLRFacturasEmitidas(header, inv_dict)
                    res_line = res["RegistroRespuestaConsultaLRFacturasEmitidas"][0]
                elif mapping_key in ["in_invoice", "in_refund"]:
                    res = serv.ConsultaLRFacturasRecibidas(header, inv_dict)
                    res_line = res["RegistroRespuestaConsultaLRFacturasRecibidas"][0]
                match_vals = self._get_match_report_values(res_line)
                inv_vals["sii_match_return"] = match_vals["sii_match_return"]
                inv_vals["sii_match_state"] = match_vals["sii_match_state"]
                inv_vals["sii_contrast_state"] = match_vals["sii_contrast_state"]
                inv_vals["sii_match_difference_ids"] = [Command.clear()] + match_vals[
                    "sii_match_difference_ids"
                ]
                document.write(inv_vals)
            except Exception as fault:
                new_cr = Registry(self.env.cr.dbname).cursor()
                env = api.Environment(new_cr, self.env.uid, self.env.context)
                document = env[document._name].browse(document.id)
                inv_vals = {
                    "sii_match_return": repr(fault),
                    "sii_contrast_state": False,
                    "sii_match_state": False,
                }
                document.write(inv_vals)
                new_cr.commit()
                new_cr.close()
                raise
