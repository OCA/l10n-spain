# Copyright 2017 Consultoría Informática Studio 73 S.L.
# Copyright 2017 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, tools


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    @tools.ormcache('company')
    def _get_dua_fiscal_position(self, company):
        dua_fiscal_position = self.env.ref(
            'l10n_es_dua.%i_fp_dua' % (company.id),
            raise_if_not_found=False
        ) or self.env['account.fiscal.position'].search([
            ('name', '=', 'Importación con DUA')
        ])
        return dua_fiscal_position

    @api.multi
    @api.depends('tax_line_ids')
    def _compute_sii_enabled(self):
        super(AccountInvoice, self)._compute_sii_enabled()
        for invoice in self.filtered('sii_enabled'):
            dua_fiscal_position = self._get_dua_fiscal_position(
                invoice.company_id)
            if dua_fiscal_position and \
                    invoice.fiscal_position_id == dua_fiscal_position and \
                    not invoice.sii_dua_invoice:
                invoice.sii_enabled = False

    @api.multi
    def _compute_dua_invoice(self):
        taxes = self._get_sii_taxes_map(['DUA'])
        for invoice in self:
            dua_fiscal_position = self._get_dua_fiscal_position(
                invoice.company_id)
            invoice.sii_dua_invoice = \
                invoice.fiscal_position_id == dua_fiscal_position and \
                invoice.tax_line_ids.filtered(lambda x: x.tax_id in taxes)

    sii_dua_invoice = fields.Boolean("SII DUA Invoice",
                                     compute="_compute_dua_invoice")

    @api.multi
    def _get_sii_invoice_dict_in(self, cancel=False):
        """
        Según la documentación de la AEAT, la operación de importación se
        registra con TipoFactura = F5, sin FechaOperacion y con el NIF de la
        propia compañia en IDEmisorFactura y Contraparte
        Más información en: 8.1.2.2.Ejemplo mensaje XML de alta de importación
        en el documento de descripción de los servicios web:
        http://bit.ly/2rGWiAI

        """
        res = super(AccountInvoice, self)._get_sii_invoice_dict_in(cancel)
        if res.get('FacturaRecibida') and self.sii_dua_invoice:
            res['FacturaRecibida']['TipoFactura'] = 'F5'
            res['FacturaRecibida'].pop('FechaOperacion', None)
            res['FacturaRecibida']['IDEmisorFactura'] = \
                {'NIF': self.company_id.vat[2:]}
            res['IDFactura']['IDEmisorFactura'] = \
                {'NIF': self.company_id.vat[2:]}
            res['FacturaRecibida']['Contraparte']['NIF'] = \
                self.company_id.vat[2:]
            res['FacturaRecibida']['Contraparte']['NombreRazon'] = \
                self.company_id.name
        return res
