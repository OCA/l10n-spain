# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import orm
from openerp.tools.translate import _

#------------------------------------------------------------------------------
# Default Spanish Account Mappings
# Format for the mappings:
#       (<source account code>, <dest account code>, <description>)
#------------------------------------------------------------------------------

_LP_ACCOUNT_MAPPING = [
    ('6', '129%', False),
    ('7', '129%', False),
]

_NLP_ACCOUNT_MAPPING = [
    ('800', '133%', False),
    ('802', '133%', False),
    ('810', '1340%0', False),
    ('811', '1341%0', False),
    ('812', '1340%0', False),
    ('813', '1341%0', False),
    ('820', '135%0', False),
    ('821', '135%0', False),
    ('830', '13', False),  # Can be any 13? account, like 130 or 133
    ('833', '13', False),  # Can be any 13? account, like 130 or 133
    ('834', '137%0', False),
    ('835', '137%0', False),
    ('835', '137%0', False),
    ('838', '133%0', False),
    ('840', '130%0', False),
    ('841', '131%0', False),
    ('842', '132%0', False),
    ('850', '115%0', False),
    ('851', '115%0', False),
    ('860', '136%0', False),
    ('862', '136%0', False),
    ('890', '133%0', False),
    ('892', '133%0', False),
    ('900', '133%', False),
    ('902', '133%', False),
    ('910', '1340%0', False),
    ('911', '1341%0', False),
    ('912', '1340%0', False),
    ('913', '1341%0', False),
    ('920', '135%0', False),
    ('921', '135%0', False),
    ('940', '130%0', False),
    ('941', '131%0', False),
    ('942', '132%0', False),
    ('950', '115%0', False),
    ('951', '115%0', False),
    ('960', '136%0', False),
    ('962', '136%0', False),
    ('990', '133%0', False),
    ('991', '133%0', False),
    ('992', '133%0', False),
    ('993', '133%0', False),
]

_C_ACCOUNT_MAPPING = [
    ('1', False, False),
    ('2', False, False),
    ('3', False, False),
    ('4', False, False),
    ('5', False, False),
]


class L10nEsFiscalyearClosing(orm.Model):
    _inherit = "account.fiscalyear.closing"

    def _get_account_mappings(self, cr, uid, fyc, mapping, context):
        """Transforms the mapping dictionary on a list of mapping lines.
        """
        account_mappings = []
        account_obj = self.pool.get('account.account')
        for source, dest, description in mapping:
            # Find the source account
            account_ids = account_obj.search(
                cr, uid, [('company_id', '=', fyc.company_id.id),
                          ('code', '=like', source)])
            source_account_id = account_ids and account_ids[0] or None
            if source_account_id:
                # Find the dest account
                account_ids = account_obj.search(
                    cr, uid, [('company_id', '=', fyc.company_id.id),
                              ('code', '=like', dest),
                              ('type', '!=', 'view')])
                dest_account_id = account_ids and account_ids[0] or None
                # Use a default description if not provided
                if not description and source_account_id:
                    description = account_obj.read(cr, uid, source_account_id,
                                                   ['name'])['name']
                account_mappings.append({
                    'name': (description if dest_account_id else
                             _('No destination account %s found for account '
                               '%s.') % (dest, source)),
                    'source_account_id': source_account_id,
                    'dest_account_id': dest_account_id or None,
                })
        return account_mappings

    def _get_lp_account_mapping(self, cr, uid, fyc, context=None):
        account_mappings = self._get_account_mappings(
            cr, uid, fyc, _LP_ACCOUNT_MAPPING, context)
        return [(0, 0, acc_map) for acc_map in account_mappings]

    def _get_nlp_account_mapping(self, cr, uid, fyc, context=None):
        account_mappings = self._get_account_mappings(
            cr, uid, fyc, _NLP_ACCOUNT_MAPPING, context)
        return [(0, 0, acc_map) for acc_map in account_mappings]

    def _get_c_account_mapping(self, cr, uid, fyc, context=None):
        account_mappings = self._get_account_mappings(
            cr, uid, fyc, _C_ACCOUNT_MAPPING, context)
        return [(0, 0, acc_map) for acc_map in account_mappings]
