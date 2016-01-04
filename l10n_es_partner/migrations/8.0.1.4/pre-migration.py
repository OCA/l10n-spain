# -*- coding: utf-8 -*-
# © 2016 Diagram Software, S.L. (http://diagram.es)
#        Cristian Moncho <cristian.moncho@diagram.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

__name__ = ('Evita el borrado de los bancos ya existentes.')


def prevent_banks_deletion(cr):
    cr.execute("""
        UPDATE ir_model_data
        SET noupdate = True
        WHERE module = 'l10n_es_partner' AND
              name LIKE 'res_bank_es_%' AND
              noupdate IS False""")


def migrate(cr, version):
    prevent_banks_deletion(cr)
