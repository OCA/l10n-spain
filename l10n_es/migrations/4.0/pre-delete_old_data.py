# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008-2010 Zikzakmedia S.L. (http://zikzakmedia.com)
#                            Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2012-2013, Grupo OPENTIA (<http://opentia.com>)
#                            Dpto. Consultoría <consultoria@opentia.es>
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
__name__ = ("Delete old account chart template data")


def migrate(cr, version):
    if not version:
        return
    # This needs to be in this order to avoid null errors on required fields
    # because "ON DELETE set null" are set on some tables
    models = [
        "ir.sequence",
        "ir.actions.todo",
        "account.fiscal.position.account.template",
        "account.fiscal.position.tax.template",
        "account.fiscal.position.template",
        "account.account.template",
        # Not possible because it's also linked to account.account
        #"account.account.type",
        "account.tax.template",
        "account.tax.code.template",
        "account.chart.template",
    ]
    # Delete data
    for model in models:
        cr.execute("""DELETE FROM
                          %(table)s
                      WHERE
                          id
                      IN
                          (SELECT res_id FROM ir_model_data AS imd
                           WHERE imd.module='l10n_es'
                           AND imd.model='%(model)s')
                   """
                   % ({'table': model.replace('.', '_'), 'model': model}))
    # Delete XML IDs
    cr.execute("DELETE FROM ir_model_data WHERE module='l10n_es'")
