# -*- coding: utf-8 -*-
##############################################################################
#
#    account_balance_reporting module for OpenERP,


#    Copyright (C) 2011 SYLEAM Info Services (<http://www.syleam.fr/>)
#              Jean-Sébastien SUZANNE <jean-sebastien.suzanne@syleam.fr>
#
#    This file is a part of account_balance_reporting
#
#    account_balance_reporting is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    account_balance_reporting is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import netsvc
logger = netsvc.Logger()

def migrate(cr, v):
    """
    a new model for account.balance.reporting was created
    we must link it with ir.model.data
    """
    # affect good ir.model in ir.model.data
    logger.notifyChannel('account_balance_reporting', netsvc.LOG_INFO, 'put ir.model(account.balance.reporting).id in ir.model.data(model_account_balance_reporting).res_id')
    cr.execute("UPDATE ir_model_data SET res_id=(SELECT id FROM ir_model WHERE name='account.balance.reporting') WHERE module='account_balance_reporting' AND name='model_account_balance_reporting'")


    cr.commit()
    logger.notifyChannel('account_balance_reporting', netsvc.LOG_INFO, 'All tables was renamed')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
