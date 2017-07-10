# -*- coding: utf-8 -*-
# Copyright 2017 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.osv import osv, fields


class AccountFiscalPosition(osv.Model):
    _inherit = 'account.fiscal.position'

    _columns = {
        'sii_registration_key_sale': fields.many2one(
            'aeat.sii.mapping.registration.keys',
            'Default SII Registration Key for Sales',
            domain=[('type', '=', 'sale')]),
        'sii_registration_key_purchase': fields.many2one(
            'aeat.sii.mapping.registration.keys',
            'Default SII Registration Key for Purchases',
            domain=[('type', '=', 'purchase')]),

        'sii_active': fields.boolean(
            string='SII Active', copy=False, default=True,
            help='Enable SII for this fiscal position?'),
        'sii_enabled': fields.related('company_id', 'sii_enabled', type='boolean', string='Enable SII'),

        'sii_no_taxable_cause': fields.selection([
            ('ImportePorArticulos7_14_Otros',
             'No sujeta - No sujeción artículo 7, 14, otros'),
            ('ImporteTAIReglasLocalizacion',
             'Operaciones no sujetas en el TAI por reglas de localización'),
        ], string="SII No taxable cause"),
        'sii_exempt_cause': fields.selection(
            string="SII Exempt Cause",
            selection=[('none', 'None'),
                       ('E1', '[E1] Art. 20: Operaciones interiores exentas'),
                       ('E2', '[E2] Art. 21: Exenciones en las exportaciones de '
                              'bienes'),
                       ('E3', '[E3] Art. 22: Exenciones en las operaciones '
                              'asimiladas a las exportaciones'),
                       ('E4', '[E4] Art. 23 y 24: Exenciones relativas a '
                              'regímenes aduaneros y fiscales. Exenciones zonas '
                              'francas, depósitos francos y otros depósitos.'),
                       ('E5', '[E5] Art. 25: Exenciones en las entregas de bienes '
                              'destinados a otro estado miembro.'),
                       ('E6', '[E6] Otros')]),

        'sii_partner_identification_type' : fields.selection(
            selection=[('1', 'Nacional'), ('2', 'Intracomunitario'), ('3', 'Exportación')],
            string="Tipo de Identificación",)

    }

    def _default_sii_exempt_cause(self, cr, uid, ids):
        default_dict = self.pool['product.template'].default_get(['sii_exempt_cause'])
        return default_dict.get('sii_exempt_cause')

    # _defaults = {
    #                 'sii_no_taxable_cause': 'ImportePorArticulos7_14_Otros',
    #                 'sii_exempt_cause': 'none'
    #             },
