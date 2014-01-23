# -*- coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

def migrate(cr, version):
    if not version:
        return
    models = [
        "workflow.transition",
        "workflow.activity",
        "workflow",
    ]
    models_dict = {
        "workflow.transition": "wkf_transition",
        "workflow.activity": "wkf_activity",
        "workflow": "wkf",
    }
    # Delete workflow workitems
    cr.execute("""DELETE FROM
                      wkf_workitem
                  WHERE
                      act_id
                  IN
                      (SELECT id FROM
                          wkf_activity
                       WHERE
                           wkf_id
                       IN
                           (SELECT id FROM wkf
                           WHERE wkf.osv='l10n.es.aeat.mod303.report'))
               """)
    # Delete workflow instances
    cr.execute("""DELETE FROM
                      wkf_instance
                  WHERE
                      wkf_id
                  IN
                      (SELECT id FROM wkf
                       WHERE wkf.osv='l10n.es.aeat.mod303.report')
               """)
    # Delete rest of the data
    for model in models:
        cr.execute("""DELETE FROM
                          %(table)s
                      WHERE
                          id
                      IN
                          (SELECT res_id FROM ir_model_data AS imd
                           WHERE imd.module='l10n_es_aeat_mod303'
                           AND imd.model='%(model)s')
                   """ % ({'table': models_dict[model], 'model': model}))
    # Delete XML IDs
    cr.execute("""DELETE FROM
                      ir_model_data
                  WHERE
                      module='l10n_es_aeat_mod303'
                  AND
                      model IN %s
               """, (tuple(models),))
