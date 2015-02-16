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
import logging
import codecs


_logger = logging.getLogger(__name__)


def gen_bank_data_xml(src_path, dest_path):
    from xlrd import open_workbook
    # Abre el archivo que contine la información de los bancos
    try:
        book = open_workbook(src_path)
    except IOError:
        _logger.info("Archivo REGBANESP_CONESTAB_A.XLS no encontrado.")
        return
    sheet = book.sheet_by_index(0)
    # Prepara el archivo resultante
    output = codecs.open(dest_path, mode='w', encoding='utf-8')
    output.write("<?xml version='1.0' encoding='UTF-8'?>\n")
    output.write("<openerp>\n")
    output.write("    <data>\n")
    # Genera los nuevos registros de los bancos
    for row_index in range(1, sheet.nrows):
        row = sheet.row_values(row_index)
        if not row[29]:
            continue
        name = "res_bank_es_%s" % row[1]
        street = row[7] + '. ' + row[8] + ', ' + row[9] + ' ' + row[10]
        output.write('        <record id="%s" model="res.bank">\n' %
                     name)
        output.write('            <field name="name">%s</field>\n' % (
                     row[40].replace(u'\x26', 'Y')))
        output.write('            <field name="lname">%s</field>\n' % (
                     row[4].replace(u'\x26', 'Y')))
        output.write('            <field name="code">%s</field>\n' % (
                     row[1]))
        output.write('            <field name="bic">%s</field>\n' % (
                     row[29]))
        output.write('            <field name="vat">%s</field>\n' % (
                     row[6]))
        output.write('            <field name="street">%s</field>\n' %
                     (street))
        output.write('            <field name="city">%s</field>\n' % (
                     row[12]))
        output.write('            <field name="zip">%s</field>\n' % (
                     row[11]))
        output.write('            <field name="phone">'
                     '%s</field>\n' % row[16])
        output.write('            <field name="fax">%s</field>\n' % (
                     row[18]))
        output.write('            <field name="website">%s</field>\n' %
                     (row[19]))
        output.write('            <field eval="1" name="active"/>\n')
        output.write('            <field name="state"'
                     ' ref="l10n_es_toponyms.ES%s"/>\n' % (
                         row[11] and row[11][:-3].zfill(2) or False))
        output.write('            <field name="country"'
                     ' ref="base.es"/>\n')
        output.write('        </record>\n')
    output.write("    </data>\n")
    output.write("</openerp>\n")
    output.close()
    _logger.info("data_banks.xml generado correctamente.")

if __name__ == "__main__":
    gen_bank_data_xml('REGBANESP_CONESTAB_A.XLS', "../wizard/data_banks.xml")
