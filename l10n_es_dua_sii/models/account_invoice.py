# -*- coding: utf-8 -*-
# (c) 2017 Consultoría Informática Studio 73 S.L.
# (c) 2021 Punt Sistemes S.L.U.
# Copyright 2017 Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, tools


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    @tools.ormcache('company')
    def _get_dua_fiscal_position(self, company):
        return self.env.ref(
            'l10n_es_dua.%i_fp_dua' % company.id, raise_if_not_found=False
        ) or self.env['account.fiscal.position'].search([
            ('name', '=', 'Importación con DUA'),
            ('company_id', '=', company.id),
        ])

    @api.multi
    @api.depends('sii_dua_invoice')
    def _compute_sii_enabled(self):
        super()._compute_sii_enabled()
        self.filtered(lambda x: x.sii_enabled
                      and x.fiscal_position_id.name == 'Importación con DUA'
                      and not x.sii_dua_invoice).update({'sii_enabled': False})

    @api.multi
    @api.depends('company_id', 'fiscal_position_id', 'tax_line_ids')
    def _compute_dua_invoice(self):
        for invoice in self:
            taxes = invoice._get_sii_taxes_map(['DUA'])
            dua_fiscal_position = self._get_dua_fiscal_position(
                invoice.company_id)
            invoice.sii_dua_invoice = (
                invoice.fiscal_position_id == dua_fiscal_position
                and invoice.tax_line_ids.filtered(lambda x: x.tax_id in taxes))


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
            nif = self.company_id.vat
            if nif.upper().startswith('ES'):
                nif = nif[2:]
            res['FacturaRecibida']['IDEmisorFactura'] = {'NIF': nif}
            res['IDFactura']['IDEmisorFactura'] = {'NIF': nif}
            res['FacturaRecibida']['Contraparte']['NIF'] = nif
            res['FacturaRecibida']['Contraparte']['NombreRazon'] = \
                self.company_id.name
        return res
