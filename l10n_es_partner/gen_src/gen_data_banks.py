# -*- coding: utf-8 -*-
# © 2014 Ismael Calvo <ismael.calvo@factorlibre.com>
# © 2016 Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import codecs
from datetime import datetime
import os
try:
    import xlrd
except ImportError:
    xlrd = None


_logger = logging.getLogger(__name__)


class XlsDictReader:
    """An XLS reader which will iterate over lines in the given file, taking
    first column as the keys for the data dictionary.
    """
    def __init__(self, path, sheet_number=0):
        if not xlrd:
            raise Exception("Librería xlrd no encontrada.")
        self.workbook = xlrd.open_workbook(path)
        self.sheet = self.workbook.sheet_by_index(sheet_number)
        self.header = [self.sheet.cell_value(0, ncol) for ncol in
                       range(self.sheet.ncols)]
        self.nrow = 1

    def next(self):
        if self.nrow >= self.sheet.nrows:
            raise StopIteration
        vals = []
        for ncol in range(self.sheet.ncols):
            val = self.sheet.cell_value(self.nrow, ncol)
            cell_type = self.sheet.cell_type(self.nrow, ncol)
            if cell_type == xlrd.XL_CELL_DATE:
                vals.append(datetime(
                    *xlrd.xldate_as_tuple(val, self.workbook.datemode)))
            elif cell_type == xlrd.XL_CELL_BOOLEAN:
                vals.append(bool(val))
            else:
                vals.append(val)
        self.nrow += 1
        return dict((self.header[x], vals[x]) for x in range(len(self.header)))

    def __iter__(self):
        return self


def escape(data):
    if isinstance(data, (int, float)):
        data = unicode(int(data))
    chars = [('&', '&amp;'), ('>', '&gt;'), ('<', '&lt;'), ('"', "&quot;"),
             ("'", "&apos;")]
    for c in chars:
        data = data.replace(*c)
    return data


def gen_bank_data_xml(src_path, dest_path):
    # Leer tabla estática de BICs
    indent = "    "
    bics = {}
    reader = XlsDictReader(os.path.join(os.path.dirname(__file__), "bics.xls"))
    for row in reader:
        bics[row['ENTIDAD']] = row['BIC']
    # Abrir el archivo que contine la información de los bancos
    try:
        reader = XlsDictReader(src_path)
    except IOError:
        _logger.error("Archivo '%s' no encontrado." % src_path)
        return
    # Preparar el archivo resultante
    output = codecs.open(dest_path, mode='w', encoding='utf-8')
    output.write("<?xml version='1.0' encoding='UTF-8'?>\n")
    output.write("<odoo>\n")
    # Genera los nuevos registros de los bancos
    for row in reader:
        if row['FCHBAJA']:
            continue
        name = "res_bank_es_%s" % row['COD_BE']
        numero = (int(row['NUMEROVIA']) if
                  isinstance(row['NUMEROVIA'], float) else row['NUMEROVIA'])
        street = '%s. %s, %s' % (row['SIGLAVIA'], row['NOMBREVIA'], numero)
        output.write(indent + '<record id="%s" model="res.bank">\n' % name)
        output.write(indent * 2 + '<field name="name">%s</field>\n' %
                     escape(row['NOMCOMERCIAL'] or row['ANAGRAMA']))
        output.write(indent * 2 + '<field name="lname">%s</field>\n' %
                     escape(row['NOMBRE105']))
        output.write(indent * 2 + '<field name="code">%s</field>\n' %
                     escape(row['COD_BE']))
        # Han quitado el BIC del listado - Lo busco en una tabla estática
        if bics.get(row['COD_BE']):
            output.write(indent * 2 + '<field name="bic">%s</field>\n' %
                         bics[row['COD_BE']])
        output.write('        <field name="street">%s</field>\n' %
                     escape(street))
        if row['RESTODOM']:
            output.write(indent * 2 + '<field name="street2">%s</field>\n' %
                         escape(row['RESTODOM']))
        if row['DIRINTERNET']:
            output.write(indent * 2 + '<field name="website">%s</field>\n' %
                         escape(row['DIRINTERNET'].lower()))
        if row['CODIGOCIF']:
            output.write(indent * 2 + '<field name="vat">%s</field>\n' %
                         escape(row['CODIGOCIF']))
        output.write(indent * 2 + '<field name="city">%s</field>\n' %
                     escape(row['POBLACION']))
        output.write('        <field name="zip">%s</field>\n' %
                     escape(row['CODPOSTAL']))
        if row['TELEFONO']:
            output.write(indent * 2 + '<field name="phone">%s</field>\n' %
                         escape(row['TELEFONO']))
        if row['NUMFAX']:
            output.write(indent * 2 + '<field name="fax">%s</field>\n' %
                         escape(row['NUMFAX']))
        output.write('        <field eval="1" name="active"/>\n')
        output.write(
            indent * 2 +
            '<field name="state" ref="l10n_es_toponyms.ES%s"/>\n' %
            (row['CODPOSTAL'] and
             escape(unicode(int(row['CODPOSTAL']))[:-3].zfill(2)) or False))
        output.write(indent * 2 + '<field name="country" ref="base.es"/>\n')
        output.write(indent + '</record>\n')
    output.write("</odoo>\n")
    output.close()
    _logger.info("data_banks.xml generado correctamente.")


if __name__ == "__main__":
    dir_path = os.path.os.path.dirname(__file__)
    parent_path = os.path.abspath(os.path.join(dir_path, os.pardir))
    gen_bank_data_xml('REGBANESP_CONESTAB_A.xls',
                      os.path.join(parent_path, "wizard", "data_banks.xml"))
