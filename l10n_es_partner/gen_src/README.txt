##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2014 Factor Libre S.L (http://www.factorlibre.com)
#                       Ismael Calvo <ismael.calvo@factorlibre.com> 
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
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

Utilidad para generar el archivo de bancos apartir de la información del Banco de España
========================================================================================

1. Descargar el excel de las 'Entidades con establecimiento' de la web del
Banco de España:
http://www.bde.es/bde/es/secciones/servicios/Particulares_y_e/Registros_de_Ent/Datos_actuales/Registros_ofici_c6e37f3710fd821.html
2. Mover el archivo descargado 'REGBANESP_CONESTAB_A.XLS' a la carpeta gen_src
3. Ejecutar:
    python gen_data_banks.py
4. Se generará un archivo data_banks.xml en la carpeta wizard que sustituirá el anterior
