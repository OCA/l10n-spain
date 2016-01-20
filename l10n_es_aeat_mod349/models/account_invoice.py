# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api

OPERATION_KEYS = [
    ('E', 'E - Intra-Community supplies'),
    ('A', 'A - Intra-Community acquisition'),
    ('T', 'T - Triangular operations'),
    ('S', 'S - Intra-Community services'),
    ('I', 'I - Intra-Community services acquisitions'),
    ('M', 'M - Intra-Community supplies without taxes'),
    ('H', 'H - Intra-Community supplies without taxes '
     'delivered by legal representative')
]


class AccountInvoice(models.Model):
    """Inheritance of account invoce to add some fields:
    - operation_key: Operation key of invoice
    """
    _inherit = 'account.invoice'

    def _get_operation_key(self, fp, invoice_type):
        if not fp.intracommunity_operations:
            return False
        else:
            # TODO: Ver cómo discernir si son prestación de servicios
            if invoice_type in ('out_invoice', 'out_refund'):
                # Establecer a entrega si es de venta
                return 'E'
            else:
                # Establecer a adquisición si es de compra
                return 'A'

    @api.multi
    @api.onchange('fiscal_position')
    def onchange_fiscal_position_l10n_es_aeat_mod349(self):
        """Suggest an operation key when fiscal position changes."""
        for invoice in self:
            if invoice.fiscal_position:
                invoice.operation_key = self._get_operation_key(
                    invoice.fiscal_position, invoice.type)

    @api.model
    def create(self, vals):
        """Writes operation key value, if invoice is created in
        backgroud with intracommunity fiscal position defined"""
        if vals.get('fiscal_position') and \
                vals.get('type') and not vals.get('operation_key'):
            fp_obj = self.env['account.fiscal.position']
            fp = fp_obj.browse(vals['fiscal_position'])
            vals['operation_key'] = self._get_operation_key(fp, vals['type'])
        return super(AccountInvoice, self).create(vals)

    operation_key = fields.Selection(selection=OPERATION_KEYS,
                                     string='Operation key')
