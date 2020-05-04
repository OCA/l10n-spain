
from odoo import models, fields


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = ['res.partner', 'l10n.es.mod190.additional.data.mixin']

    include_on_aeat_mod190 = fields.Boolean(
        string='Included in mod190',
        oldname='incluir_190',
        default=False
    )
