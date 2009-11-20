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
Account renumber wizard
"""
__author__ = "Borja López Soilán (Pexego)"


import wizard
import netsvc
import pooler
from tools.translate import _

class wizard_renumber(wizard.interface):
    """
    Account renumber wizard.
    """

    ############################################################################
    # Init form
    ############################################################################

    _init_fields = {
      'journal_ids': {'string': 'Journal', 'type': 'many2many', 'relation': 'account.journal', 'required': True},
      'period_ids': {'string': 'Period', 'type': 'many2many', 'relation': 'account.period', 'required': True},
    }

    _init_form = """<?xml version="1.0" encoding="utf-8"?>
    <form string="Account renumber">
        <label string="This wizard will help you renumber one or more journals." colspan="4"/>
        <label string="Journals entries will be sorted by date and assigned sequential numbers using their journal sequence." colspan="4"/>
        <label string="" colspan="4"/>
        <newline/>
        <group string="Journals">
            <field name="journal_ids" nolabel="1"/>
        </group>
        <group string="Periods">
            <field name="period_ids" nolabel="1"/>
        </group>
    </form>"""

    ############################################################################
    # Renumber form/action
    ############################################################################

    _renumber_fields = {
      'account_move_ids': {'string': 'Account moves', 'type': 'many2many', 'relation': 'account.move', 'required': True},
    }

    _renumber_form = """<?xml version="1.0" encoding="utf-8"?>
    <form string="Renumbering done" colspan="4">
        <group string="" colspan="4">
            <label string="The next moves have been renumbered:" colspan="4"/>
            <field name="account_move_ids" readonly="1" colspan="4" nolabel="1"/>
        </group>
    </form>"""

    def _renumber_action(self, cr, uid, data, context):
        """
        Inicializa los datos del formulario final
        """
        period_ids = data['form'].get('period_ids')
        journal_ids = data['form'].get('journal_ids')

        
        if not (period_ids and journal_ids):
            raise wizard.except_wizard(_('No Data Available'), _('No records found for your selection!'))
        
        period_ids = period_ids[0][2]
        journal_ids = journal_ids[0][2]

        journal_period_ids = []

        move_facade = pooler.get_pool(cr.dbname).get('account.move')

        move_ids = move_facade.search(cr, uid, [('journal_id','in',journal_ids),('period_id','in',period_ids),('state','=','posted')], limit=0, order='date,id', context=context)

        if len(move_ids) == 0:
            raise wizard.except_wizard(_('No Data Available'), _('No records found for your selection!'))

        sequences_seen = []

        for move in move_facade.browse(cr, uid, move_ids):
            #
            # Get the sequence to use for this move
            #
            sequence = move.journal_id.sequence_id
            if not sequence.id in sequences_seen:
                # First time we see this sequence, reset it
                pooler.get_pool(cr.dbname).get('ir.sequence').write(cr, uid, [sequence.id], {'number_next': 1})
                sequences_seen.append(sequence.id)
                
            #
            # Generate and write the new move number
            #
            new_name = pooler.get_pool(cr.dbname).get('ir.sequence').get_id(cr, uid, sequence.id, context=context)
            move_facade.write(cr, uid, [move.id], {'name': new_name})

        vals = {
            'account_move_ids': move_ids,
        }
        return vals



    ############################################################################
    # States
    ############################################################################


    states = {
        'init': {
            'actions': [],
            'result': {'type':'form', 'arch': _init_form, 'fields': _init_fields, 'state':[('end','Cancel', 'gtk-cancel', True),('renumber','Continue', 'gtk-go-forward', True)]}
        },
        'renumber': {
            'actions': [_renumber_action],
            'result': {'type':'form', 'arch': _renumber_form, 'fields': _renumber_fields, 'state':[('end','Done', 'gtk-ok', True)]}
        },
        'close': {
            'actions': [],
            'result': {'type': 'state', 'state':'end'}
        }
    }
wizard_renumber('account_renumber.renumber_wizard')

