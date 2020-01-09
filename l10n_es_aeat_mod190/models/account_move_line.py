# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    aeat_perception_key_id = fields.Many2one(
        comodel_name='l10n.es.aeat.report.perception.key',
        string='Clave percepción',
        oldname='performance_key',
        help='Se consignará la clave alfabética que corresponda a las '
             'percepciones de que se trate.',
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
    )
