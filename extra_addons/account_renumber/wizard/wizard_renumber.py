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
import time
from datetime import datetime

class wizard_renumber(wizard.interface):
    """
    Account renumber wizard.
    """

    ############################################################################
    # Helper methods
    ############################################################################

    def _process(self, s, date_to_use=None):
        """
        Based on ir_sequence._process. We need to have our own method
        as ir_sequence one will always use the current date.
        We will use the given date instead.
        """
        date_to_use = date_to_use or time
        return (s or '') % {
            'year': date_to_use.strftime('%Y'),
            'month': date_to_use.strftime('%m'),
            'day': date_to_use.strftime('%d'),
            'y': date_to_use.strftime('%y'),
            'doy': date_to_use.strftime('%j'),
            'woy': date_to_use.strftime('%W'),
            'weekday': date_to_use.strftime('%w'),
            'h24': time.strftime('%H'),
            'h12': time.strftime('%I'),
            'min': time.strftime('%M'),
            'sec': time.strftime('%S'),
        }

    def get_id(self, cr, uid, sequence_id, test='id=%s', context=None, date_to_use=None):
        """
        Based on ir_sequence.get_id. We need to have our own method
        as ir_sequence one will always use the current date for the prefix
        and sufix processing. We will use the given date instead.
        """
        try:
            cr.execute('SELECT id, number_next, prefix, suffix, padding FROM ir_sequence WHERE '+test+' AND active=%s FOR UPDATE', (sequence_id, True))
            res = cr.dictfetchone()
            if res:
                cr.execute('UPDATE ir_sequence SET number_next=number_next+number_increment WHERE id=%s AND active=%s', (res['id'], True))
                if res['number_next']:
                    return self._process(res['prefix'], date_to_use=date_to_use) + '%%0%sd' % res['padding'] % res['number_next'] + self._process(res['suffix'], date_to_use=date_to_use)
                else:
                    return self._process(res['prefix'], date_to_use=date_to_use) + self._process(res['suffix'], date_to_use=date_to_use)
        finally:
            cr.commit()
        return False

    ############################################################################
    # Init form
    ############################################################################

    _init_fields = {
      'journal_ids': {'string': 'Journals', 'type': 'many2many', 'relation': 'account.journal', 'required': True, 'help': "Journals to renumber"},
      'period_ids': {'string': 'Periods', 'type': 'many2many', 'relation': 'account.period', 'required': True, 'help': 'Fiscal periods to renumber'},
      'number_next': {'string': 'First Number', 'type': 'integer', 'required': True, 'default': 1, 'help': "Journal sequences will start counting on this number" },
    }

    _init_form = """<?xml version="1.0" encoding="utf-8"?>
    <form string="Renumber Account Moves">
        <label string="This wizard will help you renumber one or more journals." colspan="4"/>
        <label string="Posted moves from those journals will be sorted by date and then assigned sequential numbers using their journal sequence." colspan="4"/>
        <label string="" colspan="4"/>
        <newline/>
        <group string="Journals and periods to consider" colspan="4">
            <field name="journal_ids" colspan="4"/>
            <field name="period_ids" colspan="4"/>
        </group>
        <group string="Sequence options" colspan="4">
            <field name="number_next"/>
        </group>
    </form>"""

    ############################################################################
    # Renumber form/action
    ############################################################################

    _renumber_fields = {
      'journal_ids': {'string': 'Journals', 'type': 'many2many', 'relation': 'account.journal', 'help': "Renumbered journals"},
      'period_ids': {'string': 'Periods', 'type': 'many2many', 'relation': 'account.period', 'help': 'Renumbered fiscal periods'},
    }

    _renumber_form = """<?xml version="1.0" encoding="utf-8"?>
    <form string="Renumber Account Moves - Done" colspan="4">
        <group string="" colspan="4">
            <label string="The moves of the selected journals and periods have been renumbered." colspan="4"/>
            <label string="" colspan="4"/>
            <label string="You may now review them using the show results button." colspan="4"/>
        </group>
    </form>"""

    def _renumber_action(self, cr, uid, data, context):
        """
        Action that renumbers all the posted moves on the given
        journal and periods, and returns their ids.
        """
        logger = netsvc.Logger()

        period_ids = data['form'].get('period_ids')
        journal_ids = data['form'].get('journal_ids')
        number_next = data['form'].get('number_next', 1)

        if not (period_ids and journal_ids):
            raise wizard.except_wizard(_('No Data Available'), _('No records found for your selection!'))
        
        period_ids = period_ids[0][2]
        journal_ids = journal_ids[0][2]


        logger.notifyChannel("account_renumber", netsvc.LOG_DEBUG, "Searching for account moves to renumber.")

        move_facade = pooler.get_pool(cr.dbname).get('account.move')
        move_ids = move_facade.search(cr, uid, [('journal_id','in',journal_ids),('period_id','in',period_ids),('state','=','posted')], limit=0, order='date,id', context=context)

        if len(move_ids) == 0:
            raise wizard.except_wizard(_('No Data Available'), _('No records found for your selection!'))

        sequences_seen = []

        logger.notifyChannel("account_renumber", netsvc.LOG_DEBUG, "Renumbering %d account moves." % len(move_ids))

        for move in move_facade.browse(cr, uid, move_ids):
            #
            # Get the sequence to use for this move
            #
            sequence = move.journal_id.sequence_id
            if not sequence.id in sequences_seen:
                # First time we see this sequence, reset it
                pooler.get_pool(cr.dbname).get('ir.sequence').write(cr, uid, [sequence.id], {'number_next': number_next})
                sequences_seen.append(sequence.id)
                
            #
            # Generate (using our own get_id) and write the new move number
            #
            date_to_use = datetime.strptime(move.date, '%Y-%m-%d')
            new_name = self.get_id(cr, uid, sequence.id, context=context, date_to_use=date_to_use)
            move_facade.write(cr, uid, [move.id], {'name': new_name})


        logger.notifyChannel("account_renumber", netsvc.LOG_DEBUG, "%d account moves renumbered." % len(move_ids))

        vals = {
            'journal_ids': journal_ids,
            'period_ids': period_ids,
        }
        return vals


    ############################################################################
    # Show results action
    ############################################################################

    def _show_results_action(self, cr, uid, data, context):
        """
        Action that shows the list of (non-draft) account moves from
        the selected journals and periods, so the user can review
        the renumbered account moves.
        """
        period_ids = data['form'].get('period_ids')
        journal_ids = data['form'].get('journal_ids')

        assert (period_ids and journal_ids)

        period_ids = period_ids[0][2]
        journal_ids = journal_ids[0][2]

        cr.execute('select id,name from ir_ui_view where model=%s and type=%s', ('account.move', 'tree'))
        view_res = cr.fetchone()
        res = {
            'domain': "[('journal_id','in',%s), ('period_id','in',%s), ('state','=','posted')]" % (repr(journal_ids), repr(period_ids)),
            'name': _("Renumbered account moves"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': view_res,
            'context': context,
            'type': 'ir.actions.act_window',
        }
        return res


    ############################################################################
    # States
    ############################################################################

    states = {
        'init': {
            'actions': [],
            'result': {'type':'form', 'arch': _init_form, 'fields': _init_fields, 'state':[('end', 'Cancel', 'gtk-cancel', True),('renumber', 'Renumber', 'gtk-ok', True)]}
        },
        'renumber': {
            'actions': [_renumber_action],
            'result': {'type':'form', 'arch': _renumber_form, 'fields': _renumber_fields, 'state':[('end', 'Close', 'gtk-close', True), ('show_results', 'Show results', 'gtk-ok', True)]}
        },
        'show_results': {
            'actions': [],
            'result': {'type': 'action', 'action': _show_results_action, 'state':'end'}
        }
    }

wizard_renumber('account_renumber.renumber_wizard')

