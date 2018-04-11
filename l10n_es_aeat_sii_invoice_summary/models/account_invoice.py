# -*- coding: utf-8 -*-
# © 2017 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# © 2018 FactorLibre - Victor Rodrigo <victor.rodrigo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    is_invoice_summary = fields.Boolean('Is SII simplified invoice Summary?')
    sii_invoice_summary_start = fields.Char(
        'SII Invoice Summary: First Invoice')
    sii_invoice_summary_end = fields.Char('SII Invoice Summary: Last Invoice')

    @api.multi
    def _get_sii_invoice_dict_out(self, cancel=False):
        inv_dict = super(AccountInvoice, self)._get_sii_invoice_dict_out(
            cancel=cancel)
        if self.is_invoice_summary and \
                self.type == 'out_invoice':
            tipo_factura = 'F4'
            if self.sii_invoice_summary_start:
                if self.sii_invoice_summary_start == \
                        self.sii_invoice_summary_end:
                    tipo_factura = 'F2'
                else:
                    inv_dict['IDFactura']['NumSerieFacturaEmisor'] =\
                        self.sii_invoice_summary_start
                    inv_dict['IDFactura'][
                        'NumSerieFacturaEmisorResumenFin'] =\
                        self.sii_invoice_summary_end
            if 'FacturaExpedida' in inv_dict:
                if 'TipoFactura' in inv_dict['FacturaExpedida']:
                    inv_dict['FacturaExpedida']['TipoFactura'] = tipo_factura
                if tipo_factura == 'F4':
                    if 'Contraparte' in inv_dict['FacturaExpedida']:
                        del inv_dict['FacturaExpedida']['Contraparte']
        return inv_dict
