# © 2017 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# © 2018 FactorLibre - Victor Rodrigo <victor.rodrigo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, exceptions, models, _


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
                        'NumSerieFacturaEmisorsummarynFin'] =\
                        self.sii_invoice_summary_end
            if 'FacturaExpedida' in inv_dict:
                if 'TipoFactura' in inv_dict['FacturaExpedida']:
                    inv_dict['FacturaExpedida']['TipoFactura'] = tipo_factura
                if tipo_factura == 'F4':
                    if 'Contraparte' in inv_dict['FacturaExpedida']:
                        del inv_dict['FacturaExpedida']['Contraparte']
        return inv_dict

    def _vat_required(self):
        res = super(AccountInvoice, self)._vat_required()
        if self.is_invoice_summary:
            res = False
        return res

    @api.multi
    def _sii_check_exceptions(self):
        """Inheritable method for exceptions control when sending SII invoices.
        """
        self.ensure_one()
        if (not self.fiscal_position_id and not self.partner_id.vat and
                not self.is_invoice_summary) or \
                (self.fiscal_position_id and
                 self.fiscal_position_id.vat_required and not
                 self.partner_id.vat):
            raise exceptions.Warning(
                _("The partner has not a VAT configured.")
            )
        if not self.company_id.chart_template_id:
            raise exceptions.Warning(_(
                'You have to select what account chart template use this'
                ' company.'))
        if not self.company_id.sii_enabled:
            raise exceptions.Warning(
                _("This company doesn't have SII enabled.")
            )
