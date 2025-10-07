# Copyright 2014 Ismael Calvo <ismael.calvo@factorlibre.com>
# Copyright 2016-2017 Tecnativa - Pedro M. Baeza
# Copyright 2025 Studio73 - Pablo Cortés <pablo.cortes@studio73.es>

# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import codecs
import csv
import logging
import os

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
    "52": "ml",
}

logging.basicConfig()
_logger = logging.getLogger(__name__)


def gen_bank_data_csv(src_path, dest_path):
    bics = {}
    bic_file_path = os.path.join(os.path.dirname(__file__), "bics.csv")
    try:
        with codecs.open(bic_file_path, mode="r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                bics[row["ENTIDAD"]] = row["BIC"]
    except FileNotFoundError:
        _logger.warning("Archivo de BICs no encontrado. Se continuará sin ellos.")

    fieldnames = [
        "id",
        "name",
        "lname",
        "code",
        "bic",
        "street",
        "street2",
        "website",
        "vat",
        "city",
        "zip",
        "phone",
        "active",
        "state:id",
        "country:id",
    ]

    try:
        with (
            codecs.open(src_path, mode="r", encoding="utf-8") as infile,
            codecs.open(dest_path, mode="w", encoding="utf-8") as outfile,
        ):
            reader = csv.DictReader(infile)
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                if row.get("FCHBAJA"):
                    continue

                try:
                    numero = int(row.get("NUMEROVIA", "0"))
                except ValueError:
                    numero = 0

                street = f"{row.get('SIGLAVIA', '').title()}. {row.get('NOMBREVIA', '').title()}, {numero}"  # noqa E501

                state_ref = ""
                codpostal = row.get("CODPOSTAL", "")
                if codpostal and codpostal.isdigit():
                    province_code = codpostal[:-3].zfill(2)
                    if province_code in STATES_REPLACE_LIST:
                        state_ref = (
                            f"base.state_es_{STATES_REPLACE_LIST[province_code]}"
                        )

                new_row = {
                    "id": f"res_bank_es_{row['COD_BE']}",
                    "name": row.get("NOMCOMERCIAL", "").title()
                    or row.get("ANAGRAMA", "").title(),
                    "lname": row.get("NOMBRE105", "").title(),
                    "code": row["COD_BE"],
                    "bic": bics.get(row["COD_BE"], ""),
                    "street": street,
                    "street2": row.get("RESTODOM", "").title(),
                    "website": row.get("DIRINTERNET", "").lower(),
                    "vat": row.get("CODIGOCIF", ""),
                    "city": row.get("POBLACION", "").title(),
                    "zip": codpostal,
                    "phone": row.get("TELEFONO", ""),
                    "active": "1",
                    "state:id": state_ref,
                    "country:id": "base.es",
                }
                writer.writerow(new_row)

    except FileNotFoundError:
        _logger.error("Archivo no encontrado en la ruta: %s", src_path)
        return
    except Exception as e:
        _logger.error("Error inesperado al procesar %s: %s", src_path, e)
        return
    _logger.info("Fichero %s generado correctamente.", dest_path)


if __name__ == "__main__":
    dir_path = os.path.dirname(__file__)
    parent_path = os.path.abspath(os.path.join(dir_path, os.pardir))
    source_file = os.path.join(dir_path, "REGBANESP_CONESTAB_A.csv")
    destination_file = os.path.join(parent_path, "wizard", "data_banks.csv")
    gen_bank_data_csv(source_file, destination_file)
