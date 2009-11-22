# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP - Account renumber wizard
#    Copyright (C) 2009 Pexego Sistemas Informáticos. All Rights Reserved
#    $Id$
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

"""
Script that creates large amounts of account moves on different days,
that can be used later for testing the renumber wizard.
"""
__author__ = "Borja López Soilán (Pexego)"

import sys
import re
import xmlrpclib
import socket


def create_lots_of_account_moves(dbname, user, passwd, howmany):
    """
    Small OpenERP function that will create lots of account moves
    on the selected database, that can later be used for
    testing the renumber wizard.
    Note: The database must have demo data, and a fiscal year 2009 created.
    """
    url_template = "http://%s:%s/xmlrpc/%s"
    server = "localhost"
    port = 8069
    user_id = 0

    login_facade = xmlrpclib.ServerProxy(url_template % (server, port, 'common'))
    user_id = login_facade.login(dbname, user, passwd)
    object_facade = xmlrpclib.ServerProxy(url_template % (server, port, 'object'))
        
        
    for i in range(1, howmany):
        print "%s/%s" % (i, howmany)
        #
        # Create one account move
        #
        move_id = object_facade.execute(dbname, user_id, passwd,
                'account.move', 'create', {
                    'ref': 'Test%s' % i,
                    'type': 'journal_voucher',
                    'journal_id': 5,
                    'line_id': [
                        (0, 0, {
                            'analytic_account_id': False,
                            'currency_id': False,
                            'tax_amount': False,
                            'account_id': 2,
                            'partner_id': False,
                            'tax_code_id': False,
                            'credit': 1000.0,
                            'date_maturity': False,
                            'debit': False,
                            'amount_currency': False,
                            'ref': False,
                            'name': 'Test_l1'
                        }),
                        (0, 0, {
                            'analytic_account_id': False,
                            'currency_id': False,
                            'tax_amount': False,
                            'account_id': 4,
                            'partner_id': False,
                            'tax_code_id': False,
                            'credit': False,
                            'date_maturity': False,
                            'debit': 1000.0,
                            'amount_currency': False,
                            'ref': False,
                            'name': 'Test_l2'})
                        ],
                        'period_id': 1,
                        'date': '2009-01-%s' % ((i % 31) or 1),
                        'partner_id': False,
                        'to_check': 0
                },
                {})

        # Validate the move
        object_facade.execute(dbname, user_id, passwd,
                    u'account.move', 'button_validate', [move_id], {})
       
# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
# ------------------------------------------------------------------------
    
if __name__ == "__main__":
    if len(sys.argv) < 5:
        print u"Usage: %s <dbname> <user> <password> <howmany>" % sys.argv[0]
    else:
        create_lots_of_account_moves(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]))
    
    
    
