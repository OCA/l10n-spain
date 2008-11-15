# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                    Jordi Esteve <jesteve@zikzakmedia.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import wizard
import pooler
import base64
import time
import datetime

export_form = '''<?xml version="1.0" encoding="utf-8"?>
<form string="Export project tasks to iCal file">
    <field name="d_from"/>
    <field name="d_to"/>
</form>'''


export_fields = {
    'd_from': {'string': 'From', 'type':'date', 'required':True},
    'd_to':  {'string': 'To', 'type':'date'},
}


def _get_data(self, cr, uid, data, context={}):
    return {'d_from': time.strftime('%Y-%m-%d'),}


def _ical_date(date, offset):
    """Converts database date 2008-07-26 18:30:00 to iCal date 20080726T183000Z adding the local offset time to get UTC time"""
    date_local = datetime.datetime(int(date[:4]), int(date[5:7]), int(date[8:10]), int(date[11:13]), int(date[14:16]), int(date[17:19]))
    date_utc = date_local - offset
    return "%04i%02i%02iT%02i%02i%02iZ" % (date_utc.year, date_utc.month, date_utc.day, date_utc.hour, date_utc.minute, date_utc.second)


def _export(self, cr, uid, data, context):
    """Export project tasks to iCal file"""
    pool = pooler.get_pool(cr.dbname)
    form = data['form']
    d_from = form.get('d_from', False)
    d_to = form.get('d_to', False)
    filter = [('user_id', '=', uid)]
    if d_from:
        filter.append(('date_start', '>=', d_from + ' 00:00:00'))
    if d_to:
        filter.append(('date_start', '<=', d_to + ' 23:59:59'))

    # local offset time to UTC time
    # print time.timezone,time.altzone
    if time.daylight:
        offset = datetime.timedelta(seconds = -time.altzone)
    else:
        offset = datetime.timedelta(seconds = -time.timezone)

    tasks_num = 0
    txt_file = """BEGIN:VCALENDAR
PRODID:OpenERP project tasks
VERSION:2.0"""

    task_ids = pool.get('project.task').search(cr, uid, filter)
    for task in pool.get('project.task').browse(cr, uid, task_ids, context):
        cr.execute('select create_date, write_date from project_task where id=%d' % task.id)
        task_dates = cr.dictfetchall()[0]
        
        # Computes event date_end = date_start + planned_hours
        start = datetime.datetime(int(task.date_start[:4]), int(task.date_start[5:7]), int(task.date_start[8:10]), int(task.date_start[11:13]), int(task.date_start[14:16]), int(task.date_start[17:19]))
        #print task.planned_hours, int(task.planned_hours), (task.planned_hours-int(task.planned_hours))*60
        planned_hours = datetime.timedelta(hours=int(task.planned_hours), minutes=(task.planned_hours-int(task.planned_hours))*60)
        end = start + planned_hours - offset

        txt_file += "\n\nBEGIN:VEVENT"
        txt_file += "\nDTSTAMP:" + _ical_date(time.strftime('%Y-%m-%d %H:%M:%S'), offset)
        txt_file += "\nORGANIZER;CN=" + task.user_id.name + ":MAILTO:" + (task.user_id.address_id and task.user_id.address_id.email or '')
        txt_file += "\nCREATED:" + _ical_date(task_dates['create_date'], offset)
        txt_file += "\nUID:OpenERP.project.task.id-" + str(task.id)
        txt_file += "\nLAST-MODIFIED:" + _ical_date(task_dates['write_date'] or task_dates['create_date'], offset)
        txt_file += "\nDESCRIPTION:" + (task.description or '')
        txt_file += "\nSUMMARY:" + task.name
        txt_file += "\nLOCATION:" + (task.partner_id and task.partner_id.name or '') + '-' + (task.project_id and task.project_id.name or '')
        txt_file += "\nCATEGORIES:" + (task.type and task.type.name or '')
        txt_file += "\nDTSTART:" + _ical_date(task.date_start, offset)
        txt_file += "\nDTEND:" + "%04i%02i%02iT%02i%02i%02iZ" % (end.year, end.month, end.day, end.hour, end.minute, end.second)
        txt_file += "\nTRANSP:OPAQUE"
        txt_file += "\nEND:VEVENT"
        tasks_num += 1

    txt_file += "\n\nEND:VCALENDAR"

    return {'tasks_num':tasks_num, 'file':base64.encodestring(txt_file),}


_export_done_form = '''<?xml version="1.0" encoding="utf-8"?>
<form string="Export project tasks to iCal file">
    <field name="tasks_num"/>
    <newline/>
    <field name="file"/>
</form>'''

_export_done_fields = {
    'tasks_num': {'string':'Exported tasks', 'type':'integer', 'readonly': True},
    'file': {'string':'iCal file to save', 'type':'binary', 'required': True},
}


class project_tasks_export(wizard.interface):
    states = {
        'init': {
            'actions': [_get_data],
            'result': {'type':'form', 'arch':export_form, 'fields':export_fields, 'state':[('end','Cancel','gtk-cancel'),('export','Export','',True)]}
        },
        'export': {
            'actions': [_export],
            'result': {'type': 'form', 'arch': _export_done_form, 'fields': _export_done_fields, 'state': [('end', 'End')] }
        }
    }
project_tasks_export('project_tasks.export')
