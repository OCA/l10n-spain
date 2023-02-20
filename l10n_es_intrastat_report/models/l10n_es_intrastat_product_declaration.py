# Copyright 2009-2017 Noviat.
# Copyright 2016 - FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# Copyright 2019 - FactorLibre - Daniel Duque <daniel.duque@factorlibre.com>
# Copyright 2019 - Tecnativa - Manuel Calero
# Copyright 2019 - Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import Warning as UserError
from odoo.addons.l10n_es_aeat.models.spanish_states_mapping \
    import SPANISH_STATES


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

    def _get_intrastat_state(self, inv_line):
        """Similar logic as in product_intrastat `_get_region` method."""
        intrastat_state = False
        inv_type = inv_line.invoice_id.type
        if inv_type in ('in_invoice', 'in_refund'):
            intrastat_state = inv_line.purchase_line_id.move_ids[:1].\
                location_dest_id._get_intrastat_state()
        elif inv_type in ('out_invoice', 'out_refund'):
            so = inv_line.sale_line_ids[:1].order_id
            intrastat_state = so.warehouse_id.partner_id.state_id
        if not intrastat_state:
            intrastat_state = inv_line.company_id.partner_id.state_id
        return intrastat_state

    def _update_computation_line_vals(self, inv_line, line_vals):
        super()._update_computation_line_vals(inv_line, line_vals)
        intrastat_state = self._get_intrastat_state(inv_line)
        if intrastat_state:
            line_vals['intrastat_state_id'] = intrastat_state.id
        incoterm_id = self._get_incoterm(inv_line)
        if incoterm_id:
            line_vals['incoterm_id'] = incoterm_id.id
        if self.type == 'dispatches' and int(self.year) >= 2022:
            line_vals['partner_vat'] =\
                inv_line.invoice_id.partner_shipping_id.vat or 'QV999999999999'
            if not inv_line.invoice_id.partner_shipping_id.vat:
                note = "\n" + _(
                    "Missing partner vat on invoice %s."
                ) % inv_line.invoice_id.number
                self._note += note
            if not line_vals["product_origin_country_id"]:
                note = "\n" + _(
                    "Missing origin country on product %s."
                ) % inv_line.product_id.name_get()[0][1]
                self._note += note

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
        domain = super()._prepare_invoice_domain()
        if self.type == 'arrivals':
            domain.append(
                ('type', 'in', ('in_invoice', 'out_refund')))
        elif self.type == 'dispatches':
            domain.append(
                ('type', 'in', ('out_invoice', 'in_refund')))
        return domain

    @api.model
    def _prepare_grouped_fields(self, computation_line, fields_to_sum):
        vals = super()._prepare_grouped_fields(computation_line, fields_to_sum)
        vals['intrastat_state_id'] = computation_line.intrastat_state_id.id
        vals['incoterm_id'] = computation_line.incoterm_id.id
        if computation_line.type == 'dispatches' and\
           int(computation_line.parent_id.year) >= 2022:
            vals['partner_vat'] = computation_line.partner_vat
        return vals

    @api.model
    def _prepare_declaration_line(self, computation_lines):
        vals = super()._prepare_declaration_line(computation_lines)
        # Avoid rounding in weight
        vals['weight'] = 0.0
        for computation_line in computation_lines:
            vals['weight'] += computation_line['weight']
        if not vals['weight']:
            vals['weight'] = 1
        # Avoid rounding in fiscal value
        vals['amount_company_currency'] = 0.0
        for computation_line in computation_lines:
            vals['amount_company_currency'] += \
                (computation_line['amount_company_currency'] +
                 computation_line['amount_accessory_cost_company_currency'])
        return vals

    @api.model
    def _group_line_hashcode_fields(self, computation_line):
        res = super()._group_line_hashcode_fields(computation_line)
        res['intrastat_state_id'] = computation_line.intrastat_state_id.id
        if computation_line.type == 'dispatches' and\
           int(computation_line.parent_id.year) >= 2022:
            res['partner_vat'] = computation_line.partner_vat
        return res

    def _generate_xml(self):
        return self._generate_csv()

    def _attach_xml_file(self, xml_string, declaration_name):
        attach_id = super()._attach_xml_file(xml_string, declaration_name)
        self.ensure_one()
        attach = self.env['ir.attachment'].browse(attach_id)
        filename = '%s_%s.csv' % (self.year_month, declaration_name)
        attach.write({
            'name': filename,
            'datas_fname': filename,
        })
        return attach.id

    def _generate_csv_line(self, line):
        state_code = line.intrastat_state_id.code
        vals = (
            # Estado destino/origen
            line.src_dest_country_id.code,
            # Provincia destino/origen
            SPANISH_STATES.get(state_code, state_code),
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
            False,
            # Masa neta
            str(line.weight).replace('.', ','),
            # Unidades suplementarias
            str(line.suppl_unit_qty).replace('.', ','),
            # Valor
            str(line.amount_company_currency).replace('.', ','),
            # Valor estadístico
            str(line.amount_company_currency).replace('.', ','),
        )
        # Nº IVA-VIES asignado a la contraparte de la operación
        if self.type == 'dispatches' and int(self.year) >= 2022:
            vals = vals + (str(line.partner_vat),)
        return vals

    def _generate_csv(self):
        """Generate the AEAT csv file export."""
        rows = []
        for line in self.declaration_line_ids:
            rows.append(self._generate_csv_line(line))

        csv_string = self._format_csv(rows, ';')
        return csv_string.encode('utf-8')

    def _format_csv(self, rows, delimiter):
        csv_string = ''
        for row in rows:
            for field in row:
                csv_string += field and str(field) or ''
                csv_string += delimiter
            csv_string += '\n'
        return csv_string

    def create_xls(self):
        if self.env.context.get('computation_lines'):
            report_file = 'instrastat_transactions'
        else:
            report_file = 'instrastat_declaration_lines'
        return {
            'type': 'ir.actions.report',
            'report_type': 'xlsx',
            'report_name': 'intrastat_product.product_declaration_xls',
            'context': dict(
                self.env.context,
                report_file=report_file,
                declaration_type=self.type,
                declaration_year=self.year
            ),
            'data': {'dynamic_report': True},
        }

    @api.model
    def _xls_computation_line_fields(self):
        res = super()._xls_computation_line_fields()
        if self.env.context.get('declaration_type', False) == 'dispatches' and\
           int(self.env.context.get('declaration_year', 0)) >= 2022:
            res.append('partner_vat')
        return res

    @api.model
    def _xls_declaration_line_fields(self):
        res = super()._xls_declaration_line_fields()
        if self.env.context.get('declaration_type', False) == 'dispatches'and\
           int(self.env.context.get('declaration_year', 0)) >= 2022:
            res.append('partner_vat')
        return res


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
    partner_vat = fields.Char(
        string="Customer VAT",
    )


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
    weight = fields.Float(digits=dp.get_precision('Stock Weight'))
    amount_company_currency = fields.Float(digits=dp.get_precision('Account'))
    partner_vat = fields.Char(
        string="Customer VAT"
    )
