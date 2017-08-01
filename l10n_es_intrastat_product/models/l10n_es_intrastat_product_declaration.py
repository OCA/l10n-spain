# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# © 2016 - FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)


class L10nEsIntrastatProductDeclaration(models.Model):
    _name = 'l10n.es.intrastat.product.declaration'
    _description = "Intrastat Product Declaration for Spain"
    _inherit = ['intrastat.product.declaration', 'mail.thread']

    computation_line_ids = fields.One2many(
        comodel_name='l10n.es.intrastat.product.computation.line',
        inverse_name='parent_id',
        string='Intrastat Product Computation Lines',
        states={'done': [('readonly', True)]})
    declaration_line_ids = fields.One2many(
        comodel_name='l10n.es.intrastat.product.declaration.line',
        inverse_name='parent_id',
        string='Intrastat Product Declaration Lines',
        states={'done': [('readonly', True)]})

    def _get_intrastat_transaction(self, inv_line):
        transaction = super(
            L10nEsIntrastatProductDeclaration, self
        )._get_intrastat_transaction(inv_line)
        if not transaction:
            module = __name__.split('addons.')[1].split('.')[0]
            transaction = self.env.ref(
                '%s.intrastat_transaction_1' % module)
        return transaction

    def _get_intrastat_state(self, inv_line):
        """
        Same logic as in product intrastat _get_region method.
        """
        intrastat_state = False
        inv_type = inv_line.invoice_id.type
        if inv_line.move_line_ids:
            if inv_type in ('in_invoice', 'out_refund'):
                intrastat_state = inv_line.move_line_ids[0].location_id.\
                    get_intrastat_state()
            else:
                intrastat_state = inv_line.move_line_ids[0].location_dest_id.\
                    get_intrastat_state()
        elif inv_type in ('in_invoice', 'in_refund'):
            po_lines = self.env['purchase.order.line'].search(
                [('invoice_lines', 'in', inv_line.id)])
            if po_lines:
                po = po_lines.order_id
                intrastat_state = po.location_id.get_intrastat_state()
        elif inv_line.invoice_id.type in ('out_invoice', 'out_refund'):
            so_lines = self.env['sale.order.line'].search(
                [('invoice_lines', 'in', inv_line.id)])
            if so_lines:
                so = so_lines.order_id
                intrastat_state = so.warehouse_id.partner_id.state_id
        if not intrastat_state:
            if self.company_id.intrastat_state_id:
                intrastat_state = self.company_id.intrastat_state_id
        return intrastat_state

    def _update_computation_line_vals(self, inv_line, line_vals):
        super(L10nEsIntrastatProductDeclaration, self
              )._update_computation_line_vals(inv_line, line_vals)
        intrastat_state = self._get_intrastat_state(inv_line)
        if intrastat_state:
            line_vals['intrastat_state_id'] = intrastat_state.id

    def _gather_invoices_init(self):
        if self.company_id.country_id.code != 'ES':
            raise UserError(
                _("The Spanish Intrastat Declaration requires "
                  "the Company's Country to be equal to 'Spain'."))

    def _prepare_invoice_domain(self):
        # TODO: check with ES legislation
        """
        Both in_ and out_refund must be included in order to cover
        - credit notes with and without return
        - companies subject to arrivals or dispatches only
        """
        domain = super(
            L10nEsIntrastatProductDeclaration, self)._prepare_invoice_domain()
        if self.type == 'arrivals':
            domain.append(
                ('type', 'in', ('in_invoice', 'in_refund', 'out_refund')))
        elif self.type == 'dispatches':
            domain.append(
                ('type', 'in', ('out_invoice', 'in_refund', 'out_refund')))
        return domain

    @api.model
    def _group_line_hashcode_fields(self, computation_line):
        res = super(
            L10nEsIntrastatProductDeclaration, self
        )._group_line_hashcode_fields(computation_line)
        res['intrastat_state_id'] = computation_line.intrastat_state_id.id \
            or False
        return res

    @api.multi
    def _generate_xml(self):
        return self._generate_csv()

    @api.multi
    def _generate_csv(self):
        '''Generate the AEAT csv file export.'''

        rows = []
        for line in self.declaration_line_ids:
            # TO DO port/airport
            rows.append((
                # Estado destino/origen
                line.src_dest_country_id.code,
                # Provincia destino/origen # state_code
                line.intrastat_state_id.code,
                # Condiciones de entrega
                line.incoterm_id.code,
                # Naturaleza de la transacción
                line.transaction_id.code,
                # Modalidad de transporte
                line.transport_id.code,
                # Puerto/Aeropuerto de carga o descarga
                False,
                # Código mercancías CN8
                line.hs_code_id.local_code,
                # País origen
                line.product_origin_country_id.code,
                # Régimen estadístico
                line.transaction_id.code,
                # Peso
                str(line.weight).replace('.', ','),
                # Unidades suplementarias
                str(line.suppl_unit_qty).replace('.', ','),
                # Importe facturado
                str(line.amount_company_currency).replace('.', ','),
                # Valor estadístico
                str(line.amount_company_currency).replace('.', ','),
            ))

        csv_string = self._format_csv(rows, ';')
        return csv_string

    @api.multi
    def _format_csv(self, rows, delimiter):
        csv_string = ''
        for row in rows:
            for field in row:
                csv_string += field and str(field) or ''
                csv_string += delimiter
            csv_string += '\n'
        return csv_string


class L10nEsIntrastatProductComputationLine(models.Model):
    _name = 'l10n.es.intrastat.product.computation.line'
    _inherit = 'intrastat.product.computation.line'

    parent_id = fields.Many2one(
        comodel_name='l10n.es.intrastat.product.declaration',
        string='Intrastat Product Declaration',
        ondelete='cascade', readonly=True)
    declaration_line_id = fields.Many2one(
        comodel_name='l10n.es.intrastat.product.declaration.line',
        string='Declaration Line', readonly=True)
    intrastat_state_id = fields.Many2one(
        comodel_name='res.country.state', string='Intrastat State')


class L10nEsIntrastatProductDeclarationLine(models.Model):
    _name = 'l10n.es.intrastat.product.declaration.line'
    _inherit = 'intrastat.product.declaration.line'

    parent_id = fields.Many2one(
        comodel_name='l10n.es.intrastat.product.declaration',
        string='Intrastat Product Declaration',
        ondelete='cascade', readonly=True)
    computation_line_ids = fields.One2many(
        comodel_name='l10n.es.intrastat.product.computation.line',
        inverse_name='declaration_line_id',
        string='Computation Lines', readonly=True)
    intrastat_state_id = fields.Many2one(
        comodel_name='res.country.state', string='Intrastat State')

    @api.model
    def _prepare_grouped_fields(self, computation_line, fields_to_sum):
        vals = super(
            L10nEsIntrastatProductDeclarationLine, self
        )._prepare_grouped_fields(computation_line, fields_to_sum)
        vals['intrastat_state_id'] = computation_line.intrastat_state_id.id
        return vals
