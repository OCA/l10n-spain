# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP - Spanish account balance reports
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

{
        "name" : "Spanish account balance reports",
        "version" : "0.1",
        "author" : "Pexego",
        "website" : "http://www.pexego.es",
        "category" : "Enterprise Specific Modules",
        "description": """
Spanish official account balance reports:

- BALANCE PYMES (PGCE 2008)
- CUENTA DE PÉRDIDAS Y GANANCIAS PYMES (PGCE 2008)

Based on the annual accounts deposit models for the "Registro Mercantil":
NORMAL: http://www.mjusticia.es/cs/Satellite?blobcol=urldocumento&blobheader=application%2Fpdf&blobkey=id&blobnocache=true&blobtable=Documento&blobwhere=1161679576351&ssbinary=true
PYMES: http://www.mjusticia.es/cs/Satellite?blobcol=urldocumento&blobheader=application%2Fpdf&blobkey=id&blobnocache=true&blobtable=Documento&blobwhere=1161679576359&ssbinary=true
ABREVIADO: http://www.mjusticia.es/cs/Satellite?blobcol=urldocumento&blobheader=application%2Fpdf&blobkey=id&blobnocache=true&blobtable=Documento&blobwhere=1161679576346&ssbinary=true
            """,
        "depends" : [
                'base',
                'account',
                'l10n_chart_ES',
                'account_balance_reporting',
            ],
        "init_xml" : [
            ],
        "demo_xml" : [ ],
        "update_xml" : [
                'data/balance_pymes.xml',
                'data/pyg_pymes.xml',
            ],
        "installable": True
}
