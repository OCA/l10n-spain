# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


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

    @api.model
    def _get_invoices_by_type(
            self, partner, operation_key, date_start=None, date_end=None):
        """
        Returns invoices ids by type (supplier/customer) for dates
        """
        # Set type of invoice
        invoice_type = ('in_invoice', 'out_invoice', 'in_refund', 'out_refund')
        domain = [('partner_id', 'child_of', partner.id),
                  ('state', 'in', ['open', 'paid']),
                  ('type', 'in', invoice_type),
                  ('operation_key', '=', operation_key),
                  ('date', '>=', date_start),
                  ('date', '<=', date_end)]
        return self.search(domain)

    @api.multi
    def clean_refund_invoices(
            self, partner, date_start, date_end):
        """Separate refunds from invoices"""
        invoices = self.env['account.invoice']
        refunds = self.env['account.invoice']
        for inv in self:
            if inv.type in ('in_refund', 'out_refund'):
                if not inv.origin_invoice_ids:
                    invoices += inv
                    continue
                origin_lines = inv.origin_invoice_ids.filtered(
                    lambda record: record.state in ('open', 'paid') and
                    record.partner_id.commercial_partner_id == partner)
                for origin_line in origin_lines:
                    if (origin_line.date <= date_start or
                            origin_line.date >= date_end):
                        refunds += inv
                    else:
                        invoices += inv
            else:
                invoices += inv
        return invoices, refunds

    @api.onchange('fiscal_position_id', 'type')
    def _onchange_fiscal_position_id(self):
        if self.fiscal_position_id and self.type:
            self.operation_key = self._get_operation_key(
                self.fiscal_position_id, self.type,
            )

    @api.model
    def create(self, vals):
        """Writes operation key value, if invoice is created in
        background with intracommunity fiscal position defined"""
        if vals.get('fiscal_position_id') and \
                vals.get('type') and not vals.get('operation_key'):
            fp_obj = self.env['account.fiscal.position']
            fp = fp_obj.browse(vals['fiscal_position_id'])
            vals['operation_key'] = self._get_operation_key(fp, vals['type'])
        return super(AccountInvoice, self).create(vals)

    operation_key = fields.Selection(selection=OPERATION_KEYS,
                                     string='Operation key')
