# Copyright 2018 Studio73 - Abraham Anes
# Copyright 2019 Studio73 - Pablo Fuentes
# Copyright 2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from deepdiff import DeepDiff
from zeep.helpers import serialize_object

from odoo import _, api, exceptions, fields, models
from odoo.modules.registry import Registry


class AccountMove(models.Model):
    _inherit = "account.move"

    sii_match_sent = fields.Text(string="SII match sent", copy=False, readonly=True)
    sii_match_return = fields.Text(
        string="SII match return",
        copy=False,
        readonly=True,
    )
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
        help="- No testable: The counterpart is not suscribed to SII "
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
    )

    def _get_diffs(self, odoo_values, sii_values):
        sii_values = json.loads(json.dumps(serialize_object(sii_values)))
        dp = self.env["decimal.precision"].precision_get("Account")
        res = []
        if not DeepDiff:
            raise exceptions.UserError(
                _(
                    "You have not installed deepdiff library, "
                    "please install it in order to use this feature"
                )
            )
        diff = DeepDiff(odoo_values, sii_values)
        differences = diff.get("type_changes", {})
        differences.update(diff.get("values_changed", {}))
        for label, value in list(differences.items()):
            sii_value = value["new_value"]
            odoo_value = value["old_value"]
            label = label.split("['")[-1].replace("']", "")
            if sii_value is not None:
                # We made an explicit case for TipoImpositivo because we get
                # always 2 numbers as strings, one with decimal point separator
                # and another without
                if label == "TipoImpositivo" or isinstance(odoo_value, float):
                    sii_value = round(float(sii_value), dp)
                    odoo_value = round(float(odoo_value), dp)
                elif isinstance(odoo_value, str):
                    sii_value = sii_value.strip()
                    odoo_value = odoo_value.strip()
                if sii_value != odoo_value:
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
            if self.move_type in ["out_invoice", "out_refund"]:
                res += self._get_diffs(
                    odoo_values["FacturaExpedida"], sii_values["DatosFacturaEmitida"]
                )
            elif self.move_type in ["in_invoice", "in_refund"]:
                res += self._get_diffs(
                    odoo_values["FacturaRecibida"], sii_values["DatosFacturaRecibida"]
                )
        return list((0, 0, r) for r in res)

    def _invoice_started_jobs(self):
        for queue in self.mapped("invoice_jobs_ids"):
            if queue.state == "started":
                return False
        return True

    def _process_invoice_for_contrast_aeat(self):
        """Process invoices for contrast to the AEAT. Adds general checks from
        configuration parameters and invoice availability for SII"""
        queue_obj = self.env["queue.job"].sudo()
        for invoice in self:
            invoice = invoice.sudo().with_company(invoice.company_id)
            new_delay = invoice.with_delay(eta=False).contrast_one_invoice()
            jb = queue_obj.search([("uuid", "=", new_delay.uuid)], limit=1)
            invoice.invoice_jobs_ids |= jb

    def contrast_aeat(self):
        invoices = self.filtered(
            lambda i: (
                i.aeat_state == "sent"
                and i.state == "posted"
                and i.sii_csv
                and i.sii_enabled
            )
        )
        if not invoices._invoice_started_jobs():
            raise exceptions.UserError(
                _(
                    "You can not contrast this invoice at this moment "
                    "because there is a job running"
                )
            )
        invoices._process_invoice_for_contrast_aeat()

    def direct_contrast_aeat(self):
        self.ensure_one()
        if not self._invoice_started_jobs():
            raise exceptions.UserError(
                _(
                    "You can not contrast this invoice at this moment "
                    "because there is a job running"
                )
            )
        if (
            self.sii_csv
            and self.sii_enabled
            and self.aeat_state == "sent"
            and self.state == "posted"
        ):
            self._contrast_invoice_to_aeat()
        else:
            raise exceptions.UserError(
                _(
                    "Las facturas tienen que estar enviadas y con CSV para poder "
                    "ser contrastadas."
                )
            )

    def _get_contrast_invoice_dict_out(self):
        """Build dict with data to send to AEAT WS for invoice types:
        out_invoice and out_refund.
        :return: invoices (dict) : Dict XML with data for this invoice.
        """
        self.ensure_one()
        invoice_date = self._change_date_format(self.invoice_date)
        partner = self.partner_id.commercial_partner_id
        company = self.company_id
        ejercicio = self.date.year
        periodo = "%02d" % self.date.month
        number = self.name
        if self.thirdparty_invoice:
            number = self.thirdparty_number
        inv_dict = {
            "FiltroConsulta": {},
            "PeriodoLiquidacion": {"Ejercicio": ejercicio, "Periodo": periodo},
            "IDFactura": {
                "IDEmisorFactura": {"NIF": company.vat[2:]},
                "NumSerieFacturaEmisor": (number or "")[:60],
                "FechaExpedicionFacturaEmisor": invoice_date,
            },
        }
        if not partner.aeat_simplified_invoice:
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
        invoice_date = self._change_date_format(self.invoice_date)
        ejercicio = self.date.year
        periodo = "%02d" % self.date.month
        inv_dict = {
            "FiltroConsulta": {},
            "IDFactura": {
                "IDEmisorFactura": {
                    "NombreRazon": self.partner_id.commercial_partner_id.name[0:120],
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
        if self.move_type in ["out_invoice", "out_refund"]:
            return self._get_contrast_invoice_dict_out()
        elif self.move_type in ["in_invoice", "in_refund"]:
            return self._get_contrast_invoice_dict_in()
        return {}

    def _contrast_invoice_to_aeat(self):
        for invoice in self.filtered(lambda i: i.state == "posted"):
            serv = invoice._connect_aeat(invoice.move_type)
            header = invoice._get_aeat_header(False, True)
            inv_vals = {}
            try:
                inv_dict = invoice._get_contrast_invoice_dict()
                inv_vals["sii_match_sent"] = json.dumps(inv_dict, indent=4)
                res_line = False
                if invoice.move_type in ["out_invoice", "out_refund"]:
                    res = serv.ConsultaLRFacturasEmitidas(header, inv_dict)
                    res_line = res["RegistroRespuestaConsultaLRFacturasEmitidas"][0]
                elif invoice.move_type in ["in_invoice", "in_refund"]:
                    res = serv.ConsultaLRFacturasRecibidas(header, inv_dict)
                    res_line = res["RegistroRespuestaConsultaLRFacturasRecibidas"][0]
                inv_vals.update(
                    {"sii_contrast_state": "no_exist", "sii_match_state": False}
                )
                if res_line:
                    if res_line["DatosPresentacion"]["CSV"] == self.sii_csv:
                        cuadre_state = (
                            res_line["EstadoFactura"]["EstadoCuadre"]
                            if res_line["EstadoFactura"]
                            else False
                        )
                        if cuadre_state:
                            inv_vals.update(
                                {
                                    "sii_match_state": res_line["EstadoFactura"][
                                        "EstadoCuadre"
                                    ],
                                    "sii_contrast_state": "correct",
                                }
                            )
                            diffs = invoice._get_diffs_values(res_line)
                            if diffs:
                                inv_vals["sii_match_difference_ids"] = diffs
                                inv_vals.update({"sii_contrast_state": "partially"})
                invoice.sii_match_difference_ids.unlink()
                inv_vals["sii_match_return"] = json.dumps(
                    serialize_object(res), indent=4
                )
                invoice.write(inv_vals)
            except Exception as fault:
                new_cr = Registry(self.env.cr.dbname).cursor()
                env = api.Environment(new_cr, self.env.uid, self.env.context)
                invoice = env["account.move"].browse(self.id)
                inv_vals.update(
                    {
                        "sii_match_return": repr(fault),
                        "sii_contrast_state": False,
                        "sii_match_state": False,
                    }
                )
                invoice.write(inv_vals)
                new_cr.commit()
                new_cr.close()
                raise

    def contrast_one_invoice(self):
        self._contrast_invoice_to_aeat()
