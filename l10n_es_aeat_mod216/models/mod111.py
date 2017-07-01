# -*- coding: utf-8 -*-
# Copyright 2015 AvanzOSC - Ainara Galdona
# Copyright 2015 Pedro M. Baeza
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api


class L10nEsAeatMod111Report(models.Model):
    _inherit = 'l10n.es.aeat.mod111.report'

    @api.multi
    def _get_partner_domain(self):
        res = super(L10nEsAeatMod111Report, self)._get_partner_domain()
        partners = self.env['res.partner'].search(
            [('is_non_resident', '=', False)])
        res += [('partner_id', 'in', partners.ids)]
        return res
