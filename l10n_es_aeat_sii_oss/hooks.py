# Copyright 2022 Sygel - Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def add_sii_partner_identification_type(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    es_country_id = env.ref('base.es')
    if es_country_id:
        company_ids = env['res.company'].search([
            ('country_id', '=', es_country_id.id),
        ])
        if company_ids:
            env['account.fiscal.position'].search([
                ('company_id', 'in', company_ids.ids),
                ('name', 'ilike', 'OSS')
            ]).write({
                'sii_partner_identification_type': '2'
            })
