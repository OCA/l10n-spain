# Copyright 2022 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, tools


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    tbai_dua_invoice = fields.Boolean("TBAI DUA Invoice",
                                      compute="_compute_dua_invoice")

    @api.model
    @tools.ormcache('company')
    def _get_dua_fiscal_position_id(self, company):
        fp = self.env.ref(
            'l10n_es_dua.%i_fp_dua' % company.id, raise_if_not_found=False)
        return fp and fp.id or self.env['account.fiscal.position'].search([
            ('name', '=', 'Importación con DUA'),
            ('company_id', '=', company.id),
        ], limit=1).id

    @api.depends('company_id', 'fiscal_position_id', 'tax_line_ids')
    def _compute_dua_invoice(self):
        for invoice in self:
            tbai_dua_map = self.env['tbai.tax.map'].search(
                [('code', '=', 'DUA')]
            )
            dua_taxes = invoice.company_id.get_taxes_from_templates(
                tbai_dua_map.mapped("tax_template_ids")
            )
            invoice.tbai_dua_invoice = (
                invoice.tax_line_ids.filtered(lambda x: x.tax_id in dua_taxes))

    @api.multi
    def _get_lroe_invoice_header(self):
        self.ensure_one()
        header = super()._get_lroe_invoice_header()
        dua_fiscal_position_id = self._get_dua_fiscal_position_id(
            self.company_id)
        if self.type == 'in_invoice' and self.tbai_dua_invoice:
            header['TipoFactura'] = 'F5'
        elif self.type == 'in_invoice' and self.fiscal_position_id.id == \
                dua_fiscal_position_id:
            header['TipoFactura'] = 'F6'
        return header

    @api.multi
    def _get_lroe_in_taxes(self, sign):
        self.ensure_one()
        taxes_dict, tax_amount, not_in_amount_total = super()._get_lroe_in_taxes(sign)
        dua_fiscal_position_id = self._get_dua_fiscal_position_id(
            self.company_id)
        if self.type == 'in_invoice' and self.fiscal_position_id.id == \
                dua_fiscal_position_id and not self.tbai_dua_invoice:
            lroe_model = self.company_id.lroe_model
            for tax_line in self.tax_line_ids:
                tax_dict = self._get_lroe_tax_dict(tax_line, sign)
                tax_dict.pop('CuotaIVASoportada')
                if lroe_model == "240":
                    taxes_dict["IVA"]["DetalleIVA"].append(tax_dict)
                elif lroe_model == "140":
                    taxes_dict["RentaIVA"]["DetalleRentaIVA"].append(tax_dict)
            pass
        return taxes_dict, tax_amount, not_in_amount_total
