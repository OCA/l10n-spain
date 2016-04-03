# -*- coding: utf-8 -*-
# © 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# © 2012-2014 Ignacio Ibeas <ignacio@acysos.com>
# © 2016 Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3).

from openerp import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    comercial = fields.Char('Trade name', size=128, select=True)

    def name_search(self, cr, uid, name, args=None, operator='ilike',
                    context=None, limit=100):
        if not args:
            args = []
        partners = super(ResPartner, self).name_search(cr, uid, name, args,
                                                       operator, context,
                                                       limit)
        ids = [x[0] for x in partners]
        if name and len(ids) == 0:
            ids = self.search(cr, uid, [('comercial', operator, name)] + args,
                              limit=limit, context=context)
        return self.name_get(cr, uid, ids, context=context)
