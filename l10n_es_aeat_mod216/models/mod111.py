# Copyright 2015-2019 AvanzOSC - Ainara Galdona
# Copyright 2015-2019 Tecnativa - Pedro M. Baeza
# Copyright 2016-2019 Tecnativa - Antonio Espinosa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api


class L10nEsAeatMod111Report(models.Model):
    _inherit = 'l10n.es.aeat.mod111.report'

    @api.multi
    def _get_partner_domain(self):
        res = super(L10nEsAeatMod111Report, self)._get_partner_domain()
        res += [
            '|',
            ('partner_id.is_non_resident', '=', False),
            ('partner_id', '=', False),
        ]
        return res
