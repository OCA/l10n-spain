# -*- coding: utf-8 -*-
# Copyright 2012 - Acysos S.L. (http://acysos.com)
#                - Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2016 - Tecnativa - Angel Moya <odoo@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    vat_type = fields.Selection(
        [
            ('1', u'1 - Corresponde a un NIF'),
            ('2', u'2 - Se consigna el NIF/IVA (NIF OPERADOR '
                  u'INTRACOMUNITARIO)'),
            ('3', u'3 - Pasaporte'),
            ('4', u'4 - Documento oficial de identificación expedido por '
                  u'el país'),
            ('5', u'5 - Certificado de residencia fiscal'),
            ('6', u'6 - Otro documento probatorio'),
        ],
        string='Clave tipo de NIF',
        help="Clave número de identificación en el país de residencia. "
             "Modelo 340.",
        default="1")
