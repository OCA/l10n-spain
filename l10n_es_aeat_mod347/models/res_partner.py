# -*- coding: utf-8 -*-
# © 2004-2011 Pexego Sistemas Informáticos. (http://pexego.es)
# © 2012 NaN·Tic  (http://www.nan-tic.com)
# © 2013 Acysos (http://www.acysos.com)
# © 2013 Joaquín Pedrosa Gutierrez (http://gutierrezweb.es)
# © 2014-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
#             (http://www.serviciosbaeza.com)
# © 2016 Antiun Ingenieria S.L. - Antonio Espinosa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import fields, models, api
import logging

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    not_in_mod347 = fields.Boolean(
        "Not included in 347 report",
        help="If you mark this field, this partner will not be included in "
             "any AEAT 347 model report, independently from the total "
             "amount of its operations.", default=False)

    @api.model
    def _commercial_fields(self):
        res = super(ResPartner, self)._commercial_fields()
        res += ['not_in_mod347']
        return res

    @api.multi
    def address_get_347(self, adr_pref=None, context=None):
        """ Find contacts/addresses of the right type(s) by doing a depth-first-search
        through descendants within company boundaries (stop at entities flagged ``is_company``)
        then continuing the search at the ancestors that are within the same company boundaries.
        Defaults to partners of type ``'default'`` when the exact type is not found, or to the
        provided partner itself if no type ``'default'`` is found either. """
        adr_pref = set(adr_pref or [])
        if 'default' not in adr_pref:
            adr_pref.add('default')
        result = {}
        visited = []
        cr = self._cr
        for partner in self:
            current_partner = partner
            while current_partner:
                to_scan = [current_partner.id]
                # Scan descendants, DFS
                while to_scan:
                    record = self.browse(to_scan.pop(0))
                    visited.append(record.id)
                    cr.execute("select type from res_partner where id = %s" % (record.id))
                    res = cr.fetchone()
                    type_partner = res[0]
                    if type_partner in adr_pref and not result.get(type_partner):
                        result[type_partner] = record.id
                    if len(result) == len(adr_pref):
                        return result
                    cr.execute("select id from res_partner where parent_id = %s and id not in %s and is_company is false",(record.id, tuple(visited)))
                    res2 = cr.fetchall()
                    to_scan = map(lambda x: x[0], res2) + to_scan
                # Continue scanning at ancestor if current_partner is not a commercial entity
                if current_partner.is_company or not current_partner.parent_id:
                    break
                current_partner = current_partner.parent_id
        # default to type 'default' or the partner itself
        default = result.get('default', self.ids and self.ids[0] or False)
        for adr_type in adr_pref:
            result[adr_type] = result.get(adr_type) or default
        return result

