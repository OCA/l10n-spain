# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    aeat_perception_key_id = fields.Many2one(
        comodel_name='l10n.es.aeat.report.perception.key',
        string='Clave percepción',
        oldname='performance_key',
        help='Se consignará la clave alfabética que corresponda a las '
             'percepciones de que se trate.',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    aeat_perception_subkey_id = fields.Many2one(
        comodel_name='l10n.es.aeat.report.perception.subkey',
        string='Subclave',
        oldname='subclave',
        help='''Tratándose de percepciones correspondientes a las claves
                B, E, F, G, H, I, K y L, deberá consignarse, además, la
                subclave numérica de dos dígitos que corresponda a las
                percepciones de que se trate, según la relación de
                subclaves que para cada una de las mencionadas claves
                figura a continuación.
                En percepciones correspondientes a claves distintas de las
                mencionadas, no se cumplimentará este campo.
                Cuando deban consignarse en el modelo 190
                percepciones satisfechas a un mismo perceptor que
                correspondan a diferentes claves o subclaves de
                percepción, deberán cumplimentarle tantos apuntes o
                registros de percepción como sea necesario, de forma que
                cada uno de ellos refleje exclusivamente los datos de
                percepciones correspondientes a una misma clave y, en
                su caso, subclave.''',
        readonly=True,
        states={'draft': [('readonly', False)]},)

    @api.model
    def line_get_convert(self, line, part):
        """Copy from invoice to move lines"""
        res = super(AccountInvoice, self).line_get_convert(line, part)
        res['aeat_perception_key_id'] = line.get(
            'aeat_perception_key_id', False,
        )
        res['aeat_perception_subkey_id'] = line.get(
            'aeat_perception_subkey_id', False,
        )
        return res

    @api.model
    def invoice_line_move_line_get(self):
        """We pass on the operation key from invoice line to the move line"""
        ml_dicts = super(AccountInvoice, self).invoice_line_move_line_get()
        for ml_dict in ml_dicts:
            if 'invl_id' not in ml_dict:
                continue
            ml_dict['aeat_perception_subkey_id'] = (
                self.aeat_perception_subkey_id.id
            )
            ml_dict['aeat_perception_key_id'] = (
                self.aeat_perception_key_id.id
            )
        return ml_dicts

    @api.onchange('aeat_perception_key_id')
    def onchange_aeat_perception_key_id(self):
        if self.aeat_perception_key_id:
            self.aeat_perception_subkey_id = False
            return {'domain': {'aeat_perception_subkey_id': [
                ('aeat_perception_key_id', '=', self.aeat_perception_key_id.id)
            ]}}
        else:
            return {'domain': {'aeat_perception_subkey_id': []}}

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super()._onchange_partner_id()
        if self.fiscal_position_id.aeat_perception_key_id:
            fp = self.fiscal_position_id
            self.aeat_perception_key_id = fp.aeat_perception_key_id
            self.aeat_perception_subkey_id = fp.aeat_perception_subkey_id
        return res

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if (
            res.fiscal_position_id.aeat_perception_key_id and
            'aeat_perception_key_id' not in vals
        ):
            # Debemos hacerlo así por si generamos la factura automáticamente
            # (Como en los tests), ya que el sistema del odoo no nos permite
            # decir que campos se han cambiado con el _onchange_partner_id
            fp = res.fiscal_position_id
            res.aeat_perception_key_id = fp.aeat_perception_key_id
            res.aeat_perception_subkey_id = fp.aeat_perception_subkey_id
        return res
