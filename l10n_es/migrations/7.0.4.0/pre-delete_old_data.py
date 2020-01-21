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
from openupgradelib import openupgrade

__name__ = "Mark old account chart template data to be deleted"


def migrate(cr, version):
    # Set data as noupdate=0 to let the update remove it if possible
    openupgrade.logged_query(
        cr,
        """
        UPDATE ir_model_data
        SET noupdate = FALSE
        WHERE module = 'l10n_es' AND noupdate = TRUE
        """,
    )
