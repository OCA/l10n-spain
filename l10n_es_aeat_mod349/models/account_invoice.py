# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api, exceptions, _
from datetime import datetime, date
import calendar

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

    def _get_year_from_fy_month(self, fy, month):
        fy_start = fields.Date.from_string(fy.date_start)
        fy_stop = fields.Date.from_string(fy.date_stop)
        if fy_start.month < month:
            year = fy_start.year
        elif fy_stop.month > month:
            year = fy_stop.year
        else:
            raise exceptions.Warning(
                _('Cannot get invoices.\nProvided month is not included on '
                  'selected fiscal year'))
        return year

    @api.model
    def _get_invoices_by_type(
            self, partner, operation_key, fiscalyear=None,
            period_id=None, month=None, period_selection=None):
        """
        Returns invoices ids by type (supplier/customer) for a fiscal
        year, period or month.
        """
        assert period_selection, 'There is no period selected'
        # Set type of invoice
        invoice_type = ('in_invoice', 'out_invoice', 'in_refund', 'out_refund')
        domain = [('partner_id', 'child_of', partner.id),
                  ('state', 'in', ['open', 'paid']),
                  ('type', 'in', invoice_type),
                  ('operation_key', '=', operation_key)]
        # Invoices by fiscalyear (Annual)
        if period_selection == '0A':
            if not fiscalyear:
                raise exceptions.Warning(
                    _('Cannot get invoices.\nThere is no fiscal year '
                      'selected'))
            domain.append(('period_id', 'in',
                           [period.id for period in fiscalyear.period_ids
                            if not period.special]))
        # Invoices by period
        elif period_selection in ['1T', '2T', '3T', '4T']:
            if not period_id:
                raise exceptions.Warning(
                    _('Cannot get invoices.\nThere is no period selected'))
            domain.append(('period_id', 'in', period_id))
        # Invoices by month
        else:
            if not month and not fiscalyear:
                raise exceptions.Warning(
                    _('Cannot get invoices.\nThere is no month and/or fiscal '
                      'year selected'))
            month = int(month)
            year = self._get_year_from_fy_month(fiscalyear, month)
            month_last_day = calendar.monthrange(year, month)[1]
            date_start = datetime(year=year, month=month, day=1)
            date_stop = datetime(year=year, month=month, day=month_last_day)
            domain.append(
                ('date_invoice', '>=', fields.Date.to_string(date_start)))
            domain.append(
                ('date_invoice', '<=', fields.Date.to_string(date_stop)))
        return self.search(domain)

    @api.multi
    def clean_refund_invoices(
            self, partner, fiscalyear=None, periods=None, month=None,
            period_selection=None):
        """Separate refunds from invoices"""
        invoices = self.env['account.invoice']
        refunds = self.env['account.invoice']
        for inv in self:
            if inv.type in ('in_refund', 'out_refund'):
                if not inv.origin_invoices_ids:
                    invoices += inv
                    continue
                for origin_line in inv.origin_invoices_ids:
                    if (origin_line.state in ('open', 'paid') and
                            origin_line.partner_id.commercial_partner_id ==
                            partner):
                        if period_selection == '0A':
                            if (origin_line.period_id.id not in
                                    [period.id for period in
                                     fiscalyear.period_ids if not
                                     period.special]):
                                refunds += inv
                            else:
                                invoices += inv
                        elif period_selection in ['1T', '2T', '3T', '4T']:
                            if origin_line.period_id not in periods:
                                refunds += inv
                            else:
                                invoices += inv
                        else:
                            month = int(month)
                            year = self._get_year_from_fy_month(fiscalyear,
                                                                month)
                            if (fields.Date.from_string(
                                    origin_line.date_invoice) <
                                    date(year=year, month=month, day=1)):
                                refunds += inv
                            else:
                                invoices += inv
                        break
            else:
                invoices += inv
        return invoices, refunds

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
