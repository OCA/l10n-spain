# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2014 Factor Libre S.L (http://www.factorlibre.com)
#                       Ismael Calvo <ismael.calvo@factorlibre.com>
#    $Id$
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
from xlrd import open_workbook
import codecs

if __name__ == "__main__":
    # Abre el archivo que contine la información de los bancos
    book = False
    try:
        book = open_workbook('REGBANESP_CONESTAB_A.XLS')
    except IOError:
        print "Archivo REGBANESP_CONESTAB_A.XLS no encontrado."

    if book:
        sheet = book.sheet_by_index(0)

        # Prepara el archivo resultante
        output = codecs.open("../wizard/data_banks.xml", mode='w',
                             encoding='utf-8')
        output.write("<?xml version='1.0' encoding='UTF-8'?>\n")
        output.write("<openerp>\n")
        output.write("    <data noupdate='1'>\n")

        # Genera los nuevos registros de los bancos
        for row_index in range(1, sheet.nrows):
            row = sheet.row_values(row_index)
            name = "city_bank_" + row[40].lower().replace(
                ' ', '_').replace(u'\xf1', 'n')
            street = row[7] + '. ' + row[8] + ', ' + row[9] + ' ' + row[10]
            output.write('        <record id="%s" model="city.city">\n' % name)
            output.write('            <field name="name">%s<field/>\n' % (
                         row[40]))
            output.write('            <field name="lname">%s<field/>\n' % (
                         row[4]))
            output.write('            <field name="code">%s<field/>\n' % (
                         row[1]))
            output.write('            <field name="vat">%s<field/>\n' % (
                         row[6]))
            output.write('            <field name="street">%s<field/>\n' % (
                         street))
            output.write('            <field name="city">%s<field/>\n' % (
                         row[12]))
            output.write('            <field name="zip">%s<field/>\n' % (
                         row[11]))
            output.write('            <field name="phone">'
                         '%s<field/>\n' % row[16])
            output.write('            <field name="fax">%s<field/>\n' % (
                         row[18]))
            output.write('            <field eval="1" name="active"/>\n')
            output.write('            <field name="state"'
                         ' ref="l10n_es_topynyms.ES28"/>\n')
            output.write('            <field name="country_id"'
                         ' ref="base.es"/>\n')
            output.write('        </record>\n')
        output.write("    </data>\n")
        output.write("</openerp>\n")

        output.close()
        print "data_banks.xml generado correctamente."
