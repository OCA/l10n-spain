# Copyright 2014 Ismael Calvo <ismael.calvo@factorlibre.com>
# Copyright 2016-2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import codecs
import logging
import os
from datetime import datetime

try:
    import xlrd
except ImportError:
    xlrd = None

STATES_REPLACE_LIST = {
    "01": "vi",
    "02": "ab",
    "03": "a",
    "04": "al",
    "05": "av",
    "06": "ba",
    "07": "pm",
    "08": "b",
    "09": "bu",
    "10": "cc",
    "11": "ca",
    "12": "cs",
    "13": "cr",
    "14": "co",
    "15": "c",
    "16": "cu",
    "17": "gi",
    "18": "gr",
    "19": "gu",
    "20": "ss",
    "21": "h",
    "22": "hu",
    "23": "j",
    "24": "le",
    "25": "l",
    "26": "lo",
    "27": "lu",
    "28": "m",
    "29": "ma",
    "30": "mu",
    "31": "na",
    "32": "or",
    "33": "o",
    "34": "p",
    "35": "gc",
    "36": "po",
    "37": "sa",
    "38": "tf",
    "39": "s",
    "40": "sg",
    "41": "se",
    "42": "so",
    "43": "t",
    "44": "te",
    "45": "to",
    "46": "v",
    "47": "va",
    "48": "bi",
    "49": "za",
    "50": "z",
    "51": "ce",
    # FIXME: Switch to 'me' on v11 if the code is finally changed
    "52": "ml",
}

logging.basicConfig()
_logger = logging.getLogger(__name__)


class XlsDictReader:
    """An XLS reader which will iterate over lines in the given file, taking
    first column as the keys for the data dictionary.
    """

    def __init__(self, path, sheet_number=0):
        if not xlrd:  # pragma: no cover
            raise Exception("Librería xlrd no encontrada.")
        self.workbook = xlrd.open_workbook(path)
        self.sheet = self.workbook.sheet_by_index(sheet_number)
        self.header = [
            self.sheet.cell_value(0, ncol) for ncol in range(self.sheet.ncols)
        ]
        self.nrow = 1

    def __next__(self):
        if self.nrow >= self.sheet.nrows:
            self.nrow = 1
            raise StopIteration
        vals = []
        for ncol in range(self.sheet.ncols):
            val = self.sheet.cell_value(self.nrow, ncol)
            cell_type = self.sheet.cell_type(self.nrow, ncol)
            if cell_type == xlrd.XL_CELL_DATE:  # pragma: no cover
                vals.append(
                    datetime(*xlrd.xldate_as_tuple(val, self.workbook.datemode))
                )
            elif cell_type == xlrd.XL_CELL_BOOLEAN:  # pragma: no cover
                vals.append(bool(val))
            else:
                vals.append(val)
        self.nrow += 1
        return {self.header[x]: vals[x] for x in range(len(self.header))}

    def __iter__(self):
        self.nrow = 1
        return self


def escape(data):
    if isinstance(data, (int or float)):  # pragma: no cover
        data = str(int(data))
    chars = [
        ("&", "&amp;"),
        (">", "&gt;"),
        ("<", "&lt;"),
        ('"', "&quot;"),
        ("'", "&apos;"),
    ]
    for c in chars:
        data = data.replace(*c)
    return data


def gen_bank_data_xml(src_path, dest_path):
    indent = "    "
    bics = {}
    # Leer tabla estática de BICs. Última revisión obtenida de
    # http://www.bde.es/f/webbde/SPA/sispago/t2/TARGET2_BE_BIC.pdf
    reader = XlsDictReader(os.path.join(os.path.dirname(__file__), "bics.xls"))
    for row in reader:
        bics[row["ENTIDAD"]] = row["BIC"]
    # Abrir el archivo que contine la información de los bancos
    try:
        reader = XlsDictReader(src_path)
    except OSError:  # pragma: no cover
        _logger.error(f"File {src_path} not found.")
        return
    # Preparar el archivo resultante
    output = codecs.open(dest_path, mode="w", encoding="utf-8")
    output.write("<?xml version='1.0' encoding='UTF-8'?>\n")
    output.write("<odoo>\n")
    # Genera los nuevos registros de los bancos
    for row in reader:
        if row["FCHBAJA"]:
            continue
        name = f'res_bank_es_{row["COD_BE"]}'
        numero = (
            int(row["NUMEROVIA"])
            if isinstance(row["NUMEROVIA"], float)
            else row["NUMEROVIA"]
        )
        street = "{}. {}, {}".format(
            row["SIGLAVIA"].title(), row["NOMBREVIA"].title(), numero
        )
        output.write(indent + f'<record id="{name}" model="res.bank">\n')
        output.write(
            indent * 2
            + '<field name="name">{}</field>\n'.format(
                escape(row["NOMCOMERCIAL"].title() or row["ANAGRAMA"].title())
            )
        )
        output.write(
            indent * 2
            + f'<field name="lname">{escape(row["NOMBRE105"].title())}</field>\n'
        )
        output.write(
            indent * 2 + f'<field name="code">{escape(row["COD_BE"])}</field>\n'
        )
        # Han quitado el BIC del listado - Lo busco en una tabla estática
        if bics.get(row["COD_BE"]):
            output.write(
                indent * 2 + f'<field name="bic">{bics[row["COD_BE"]]}</field>\n'
            )
        output.write(f'        <field name="street">{escape(street)}</field>\n')
        if row["RESTODOM"]:
            output.write(
                indent * 2
                + f'<field name="street2">{escape(row["RESTODOM"].title())}</field>\n'
            )
        if row["DIRINTERNET"]:
            output.write(
                indent * 2 + f'<field name="website">'
                f'{escape(row["DIRINTERNET"].lower())}</field>\n'
            )
        if row["CODIGOCIF"]:
            output.write(
                indent * 2 + f'<field name="vat">{escape(row["CODIGOCIF"])}</field>\n'
            )
        output.write(
            indent * 2
            + f'<field name="city">{escape(row["POBLACION"].title())}</field>\n'
        )
        output.write(f'        <field name="zip">{escape(row["CODPOSTAL"])}</field>\n')
        if row["TELEFONO"]:
            output.write(
                indent * 2 + f'<field name="phone">{escape(row["TELEFONO"])}</field>\n'
            )
        output.write('        <field eval="1" name="active"/>\n')
        if row["CODPOSTAL"]:
            output.write(
                indent * 2
                + '<field name="state" ref="base.state_es_{}"/>\n'.format(
                    STATES_REPLACE_LIST[str(int(row["CODPOSTAL"]))[:-3].zfill(2)]
                )
            )
        output.write(indent * 2 + '<field name="country" ref="base.es"/>\n')
        output.write(indent + "</record>\n")
    output.write("</odoo>\n")
    output.close()
    _logger.info("data_banks.xml succesfully generated.")


if __name__ == "__main__":  # pragma: no cover
    dir_path = os.path.os.path.dirname(__file__)
    parent_path = os.path.abspath(os.path.join(dir_path, os.pardir))
    gen_bank_data_xml(
        "REGBANESP_CONESTAB_A.XLS",
        os.path.join(parent_path, "wizard", "data_banks.xml"),
    )
