# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP - Account balance reporting engine
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
Account balance report calculate wizard
"""
__author__ = "Borja López Soilán (Pexego)"


import wizard
import pooler
import netsvc

class wizard_calculate(wizard.interface):
    """
    Account balance report calculate wizard.
    This wizard just acts as a wrapper around the action_calculate
    of account_balance_report, so the user gets some feedback about the
    processing taking long time.
    """

    def _calculate_action(self, cr, uid, data, context):
        """
        Calculate the selected balance report data.
        """
        report_id = None
        if data.get('model') == 'account.balance.report':
            report_id = data.get('id')
            if report_id:
                #
                # Send the calculate signal to the balance report
                # to trigger action_calculate.
                #
                wf_service = netsvc.LocalService('workflow')
                wf_service.trg_validate(uid, 'account.balance.report', report_id, 'calculate', cr)
        return 'close'


    states = {
        'init': {
            'actions': [],
            'result': {'type':'choice', 'next_state': _calculate_action}
        },
        'close': {
            'actions': [],
            'result': {'type': 'state', 'state':'end'}
        }
    }
wizard_calculate('account_balance_report.calculate_wizard')

