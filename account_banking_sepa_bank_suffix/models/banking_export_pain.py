# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP - Account banking sepa bank suffix
#    Copyright (C) 2016 Comunitea Servicios Tecnológicos.
#    Omar Castiñeira Saavedra - omar@comunitea.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api


class BankingExportPain(models.AbstractModel):
    _inherit = 'banking.export.pain'

    @api.model
    def generate_initiating_party_block(self, parent_node, gen_args):
        res = super(BankingExportPain, self).\
            generate_initiating_party_block(parent_node, gen_args)

        if self.payment_order_ids[0].mode.suffix:
            other_id_code = parent_node.xpath('//InitgPty/Id/OrgId/Othr/Id')
            if other_id_code:
                initiating_party_identifier =\
                    self.payment_order_ids[0].company_id.\
                    initiating_party_identifier
                other_id_code[0].text = initiating_party_identifier[:-3] + \
                    self.payment_order_ids[0].mode.suffix

        return res

    @api.model
    def generate_creditor_scheme_identification(
            self, parent_node, identification, identification_label,
            eval_ctx, scheme_name_proprietary, gen_args):

        res = super(BankingExportPain, self).\
            generate_creditor_scheme_identification(parent_node,
                                                    identification,
                                                    identification_label,
                                                    eval_ctx,
                                                    scheme_name_proprietary,
                                                    gen_args)
        if self.payment_order_ids[0].mode.suffix:
            other_id_code = parent_node.\
                xpath('//PrvtId/Othr/Id')
            if other_id_code:
                sepa_creditor_identifier = self.\
                    _prepare_field(identification_label, identification,
                                   eval_ctx, gen_args=gen_args)
                other_id_code[0].text = sepa_creditor_identifier[:4] + \
                    self.payment_order_ids[0].mode.suffix + \
                    sepa_creditor_identifier[7:]

        return res
