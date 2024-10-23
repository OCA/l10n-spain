# Copyright 2022 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools


class AccountMove(models.Model):
    _inherit = "account.move"

    tbai_dua_invoice = fields.Boolean(
        "TBAI DUA Invoice", compute="_compute_tbai_dua_invoice"
    )

    @api.model
    @tools.ormcache("company")
    def _get_dua_fiscal_position_id(self, company):
        fp = self.env.ref(
            "l10n_es_dua.%i_fp_dua" % company.id, raise_if_not_found=False
        )
        return (
            fp
            and fp.id
            or self.env["account.fiscal.position"]
            .search(
                [
                    ("name", "=", "Importación con DUA"),
                    ("company_id", "=", company.id),
                ],
                limit=1,
            )
            .id
        )

    @api.depends("company_id", "fiscal_position_id", "invoice_line_ids.tax_ids")
    def _compute_tbai_dua_invoice(self):
        for invoice in self:
            taxes = invoice._get_lroe_taxes_map(["DUA"])
            invoice.tbai_dua_invoice = invoice.invoice_line_ids.filtered(
                lambda x: any([tax in taxes for tax in x.tax_ids])
            )

    def _get_lroe_invoice_header(self):
        self.ensure_one()
        header = super()._get_lroe_invoice_header()
        dua_fiscal_position_id = self._get_dua_fiscal_position_id(self.company_id)
        if self.move_type == "in_invoice" and self.tbai_dua_invoice:
            header["TipoFactura"] = "F5"
        elif (
            self.move_type == "in_invoice"
            and self.fiscal_position_id.id == dua_fiscal_position_id
        ):
            header["TipoFactura"] = "F6"
        return header

    def _get_lroe_in_taxes(self):
        self.ensure_one()
        taxes_dict, tax_amount, not_in_amount_total = super()._get_lroe_in_taxes()
        dua_fiscal_position_id = self._get_dua_fiscal_position_id(self.company_id)
        if (
            self.move_type == "in_invoice"
            and self.fiscal_position_id.id == dua_fiscal_position_id
            and not self.tbai_dua_invoice
        ):
            lroe_model = self.company_id.lroe_model
            tax_lines = self._get_tax_info().values()
            for tax_line in tax_lines:
                tax_dict = self._get_lroe_tax_dict(tax_line, tax_lines)
                tax_dict.pop("CuotaIVASoportada")
                if lroe_model == "240":
                    taxes_dict["IVA"]["DetalleIVA"].append(tax_dict)
                elif lroe_model == "140":
                    taxes_dict["RentaIVA"]["DetalleRentaIVA"].append(tax_dict)
        return taxes_dict, tax_amount, not_in_amount_total
