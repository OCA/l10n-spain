# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011
#        Pexego Sistemas Informáticos. (http://pexego.es) All Rights Reserved
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

{
        "name" : "Spanish account balance reports",
        "version" : "0.1",
        "author" : "Pexego, Zikzakmedia",
        "website" : "http://www.pexego.es",
        "category" : "Localisation/Accounting",
        "description": """Spanish official account balance reports:

- BALANCE PYMES (PGCE 2008)
- CUENTA DE PÉRDIDAS Y GANANCIAS PYMES (PGCE 2008)
- BALANCE ABREVIADO (PGCE 2008)
- CUENTA DE PÉRDIDAS Y GANANCIAS ABREVIADO (PGCE 2008)
- BALANCE NORMAL (PGCE 2008)
- CUENTA DE PÉRDIDAS Y GANANCIAS NORMAL (PGCE 2008)

Based on the annual accounts deposit models for the "Registro Mercantil":

NORMAL: http://www.mjusticia.es/cs/Satellite?blobcol=urldocumento&blobheader=application%2Fpdf&blobkey=id&blobnocache=true&blobtable=Documento&blobwhere=1161679576351&ssbinary=true

ABREVIADO: http://www.mjusticia.es/cs/Satellite?blobcol=urldocumento&blobheader=application%2Fpdf&blobkey=id&blobnocache=true&blobtable=Documento&blobwhere=1161679576346&ssbinary=true

PYMES: http://www.mjusticia.es/cs/Satellite?blobcol=urldocumento&blobheader=application%2Fpdf&blobkey=id&blobnocache=true&blobtable=Documento&blobwhere=1161679576359&ssbinary=true
            """,
        "depends" : [
                'base',
                'account',
                'l10n_es',
                'account_balance_reporting',
            ],
        "init_xml" : [
            ],
        "demo_xml" : [ ],
        "update_xml" : [
                'data/balance_pymes.xml',
                'data/pyg_pymes.xml',
                'data/balance_abreviado.xml',
                'data/pyg_abreviado.xml',
                'data/balance_normal.xml',
                'data/pyg_normal.xml',
            ],
        "installable": True
}
