# Copyright 2013-2021 Tecnativa - Pedro M. Baeza
# Copyright 2021 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)

try:
    import chardet
except ImportError:
    _logger.warning(
        "chardet library not found,  please install it "
        "from http://pypi.python.org/pypi/chardet"
    )

account_mapping = {
    "01": "4300%00",
    "02": "4100%00",
    "03": "4100%00",
    "04": "430%00",
    "05": "6800%00",
    "06": "6260%00",
    "07": "5700%00",
    "08": "6800%00",
    "09": "2510%00",
    "10": "5700%00",
    "11": "5700%00",
    "12": "5700%00",
    "13": "5730%00",
    "14": "4300%00",
    "15": "6400%00",
    "16": "6690%00",
    "17": "6690%00",
    "98": "5720%00",
    "99": "5720%00",
}

CURRENCY_ISO4217_MAP = {
    978: "EUR",
    36: "AUD",
    840: "USD",
    826: "GBP",
    756: "CHF",
    752: "SEK",
    578: "NOK",
    554: "NZD",
    392: "JPY",
    208: "DKK",
    124: "CAD",
}


class AccountStatementImport(models.TransientModel):
    _inherit = "account.statement.import"

    def _process_record_11(self, line):
        """11 - Registro cabecera de cuenta (obligatorio)"""
        st_group = {
            "entidad": line[2:6],
            "oficina": line[6:10],
            "cuenta": line[10:20],
            "fecha_ini": datetime.strptime(line[20:26], "%y%m%d"),
            "fecha_fin": datetime.strptime(line[26:32], "%y%m%d"),
            "divisa": line[47:50],
            "modalidad": line[50:51],  # 1, 2 o 3
            "nombre_propietario": line[51:77],
            "saldo_ini": float("{}.{}".format(line[33:45], line[45:47])),
            "saldo_fin": 0,
            "num_debe": 0,
            "debe": 0,
            "num_haber": 0,
            "haber": 0,
            "lines": [],
        }
        if line[32:33] == "1":  # pragma: no cover
            st_group["saldo_ini"] *= -1
        return st_group

    def _process_record_22(self, line):
        """22 - Registro principal de movimiento (obligatorio)"""
        st_line = {
            "of_origen": line[6:10],
            "fecha_oper": datetime.strptime(line[10:16], "%y%m%d"),
            "fecha_valor": datetime.strptime(line[16:22], "%y%m%d"),
            "concepto_c": line[22:24],
            "concepto_p": line[24:27],
            "importe": (float(line[28:40]) + (float(line[40:42]) / 100)),
            "num_documento": line[42:52],
            "referencia1": line[52:64].strip(),
            "referencia2": line[64:].strip(),
            "conceptos": {},
        }
        if line[27:28] == "1":
            st_line["importe"] *= -1
            st_line["tipo_registro"] = "debit"
        else:
            st_line["tipo_registro"] = "credit"
        return st_line

    def _process_record_23(self, st_line, line):
        """23 - Registros complementarios de concepto (opcionales y hasta un
        máximo de 5)"""
        conceptos = st_line.setdefault("conceptos", {})
        conceptos[line[2:4]] = (line[4:39].strip(), line[39:].strip())
        return st_line

    def _process_record_24(self, st_line, line):
        """24 - Registro complementario de información de equivalencia del
        importe (opcional y sin valor contable)"""
        st_line["divisa_eq"] = line[4:7]
        st_line["importe_eq"] = float(line[7:19]) + (float(line[19:21]) / 100)
        return st_line

    def _process_record_33(self, st_group, line):
        """33 - Registro final de cuenta"""
        st_group["num_debe"] += int(line[20:25])
        st_group["debe"] += float("{}.{}".format(line[25:37], line[37:39]))
        st_group["num_haber"] += int(line[39:44])
        st_group["haber"] += float("{}.{}".format(line[44:56], line[56:58]))
        st_group["saldo_fin"] += float("{}.{}".format(line[59:71], line[71:73]))
        if line[58:59] == "1":  # pragma: no cover
            st_group["saldo_fin"] *= -1
        # Group level checks
        debit_count = 0
        debit = 0.0
        credit_count = 0
        credit = 0.0
        for st_line in st_group["lines"]:
            if st_line["tipo_registro"] == "debit":
                debit_count += 1
                debit -= st_line["importe"]
            else:
                credit_count += 1
                credit += st_line["importe"]
        st_group["lines"] = [line for line in st_group["lines"] if line["importe"] != 0]
        if st_group["num_debe"] != debit_count:  # pragma: no cover
            raise exceptions.UserError(
                _(
                    "Number of debit records doesn't match with the defined in "
                    "the last record of account."
                )
            )
        if st_group["num_haber"] != credit_count:  # pragma: no cover
            raise exceptions.UserError(
                _(
                    "Number of credit records doesn't match with the defined "
                    "in the last record of account."
                )
            )
        if abs(st_group["debe"] - debit) > 0.005:  # pragma: no cover
            raise exceptions.UserError(
                _(
                    "Debit amount doesn't match with the defined in the last "
                    "record of account."
                )
            )
        if abs(st_group["haber"] - credit) > 0.005:  # pragma: no cover
            raise exceptions.UserError(
                _(
                    "Credit amount doesn't match with the defined in the last "
                    "record of account."
                )
            )
        # Note: Only perform this check if the balance is defined on the file
        # record, as some banks may leave it empty (zero) on some circumstances
        # (like CaixaNova extracts for VISA credit cards).
        if st_group["saldo_fin"] and st_group["saldo_ini"]:  # pragma: no cover
            balance = st_group["saldo_ini"] + credit - debit
            if abs(st_group["saldo_fin"] - balance) > 0.005:
                raise exceptions.UserError(
                    _(
                        "Final balance amount = (initial balance + credit "
                        "- debit) doesn't match with the defined in the last "
                        "record of account."
                    )
                )
        return st_group

    def _process_record_88(self, st_data, line):
        """88 - Registro de fin de archivo"""
        st_data["num_registros"] = int(line[20:26])
        # File level checks
        # Some banks (like Liderbank) are informing this record number
        # including the record 88, so checking this with the absolute
        # difference allows to bypass the error
        if (
            abs(st_data["num_registros"] - st_data["_num_records"]) > 1
        ):  # pragma: no cover
            raise exceptions.UserError(
                _(
                    "Number of records doesn't match with the defined in the "
                    "last record."
                )
            )
        return st_data

    def _parse(self, data_file):
        # st_data will contain data read from the file
        result = []
        st_data = {
            "_num_records": 0,  # Number of records really counted
            "groups": [],  # Info about each of the groups (account groups)
        }
        st_group = {}
        st_line = {}
        for raw_line in data_file.split("\n"):
            if not raw_line.strip():
                continue
            code = raw_line[0:2]
            if code == "11":
                st_group = self._process_record_11(raw_line)
                st_data["groups"].append(st_group)
            elif code == "22":
                st_line = self._process_record_22(raw_line)
                st_group["lines"].append(st_line)
            elif code == "23":
                self._process_record_23(st_line, raw_line)
            elif code == "24":
                self._process_record_24(st_line, raw_line)
            elif code == "33":
                self._process_record_33(st_group, raw_line)
                result.append(st_data["groups"])
                st_data["groups"] = []
                st_group = {}
                st_line = {}
            elif code == "88":
                self._process_record_88(st_data, raw_line)
            elif ord(raw_line[0]) == 26:  # pragma: no cover
                # CTRL-Z (^Z), is often used as an end-of-file marker in DOS
                continue
            else:  # pragma: no cover
                raise exceptions.ValidationError(
                    _("Record type %s is not valid.") % raw_line[0:2]
                )
            # Update the record counter
            st_data["_num_records"] += 1
        return result

    @api.model
    def _get_common_file_encodings(self):
        """Returns a list with commonly used encodings"""
        return ["iso-8859-1", "utf-8-sig"]

    def _check_n43(self, data_file):
        # We'll try to decode with the encoding detected by chardet first
        # otherwise, we'll try with another common encodings until success
        encodings = self._get_common_file_encodings()
        # Try to guess the encoding of the data file
        detected_encoding = chardet.detect(data_file).get("encoding", False)
        if detected_encoding:
            encodings += [detected_encoding]
        while encodings:
            try:
                data_decoded = data_file.decode(encodings.pop())
                return self._parse(data_decoded)
            except (UnicodeDecodeError, exceptions.ValidationError):
                _logger.info("Something was wrong with encodings!")
        return False

    def _get_n43_ref(self, line):
        try:
            ref1 = int(line["referencia1"])
        except ValueError:  # pragma: no cover
            ref1 = line["referencia1"]
        try:
            ref2 = int(line["referencia2"])
        except ValueError:
            ref2 = line["referencia2"]
        if not ref1:
            return line["referencia2"] or "/"
        elif not ref2:
            return line["referencia1"] or "/"
        else:  # pragma: no cover
            return "{} / {}".format(line["referencia1"], line["referencia2"])

    def _get_n43_partner_from_caixabank(self, conceptos):
        partner_obj = self.env["res.partner"]
        partner = partner_obj.browse()
        # Try to match from VAT included in concept complementary record #02
        if conceptos.get("02"):  # pragma: no cover
            vat = conceptos["02"][0][:2] + conceptos["02"][0][7:]
            if vat:
                partner = partner_obj.search([("vat", "=", vat)], limit=1)
        if not partner:
            # Try to match from partner name
            if conceptos.get("01"):
                name = conceptos["01"][0][4:] + conceptos["01"][1]
                if name and len(name) > 7:
                    partner = partner_obj.search([("name", "ilike", name)], limit=1)
        return partner

    def _get_n43_partner_from_santander(self, conceptos):
        partner_obj = self.env["res.partner"]
        partner = partner_obj.browse()
        # Try to match from VAT included in concept complementary record #01
        if conceptos.get("01"):
            if conceptos["01"][1]:
                vat = conceptos["01"][1]
                if vat:
                    partner = partner_obj.search([("vat", "ilike", vat)], limit=1)
        if not partner:
            # Try to match from partner name
            if conceptos.get("01"):
                name = conceptos["01"][0]
                if name and len(name) > 7:
                    partner = partner_obj.search([("name", "ilike", name)], limit=1)
        return partner

    def _get_n43_partner_from_bankia(self, conceptos):
        partner_obj = self.env["res.partner"]
        partner = partner_obj.browse()
        # Try to match from partner name
        if conceptos.get("01"):
            vat = conceptos["01"][0][:2] + conceptos["01"][0][7:]
            if vat:
                partner = partner_obj.search([("vat", "=", vat)], limit=1)
        return partner

    def _get_n43_partner_from_sabadell(self, conceptos):
        partner_obj = self.env["res.partner"]
        partner = partner_obj.browse()
        # Try to match from partner name
        if conceptos.get("01"):
            name = conceptos["01"][1]
            if name and len(name) > 7:
                partner = partner_obj.search([("name", "ilike", name)], limit=1)
        return partner

    def _get_n43_partner(self, line):
        if not line.get("conceptos"):  # pragma: no cover
            return self.env["res.partner"]
        partner = self._get_n43_partner_from_caixabank(line["conceptos"])
        if not partner:
            partner = self._get_n43_partner_from_santander(line["conceptos"])
        if not partner:
            partner = self._get_n43_partner_from_bankia(line["conceptos"])
        if not partner:
            partner = self._get_n43_partner_from_sabadell(line["conceptos"])
        return partner

    def _get_n43_account(self, line, journal):  # pragma: no cover
        account_obj = self.env["account.account"]
        if line["concepto_c"] and account_mapping.get(line["concepto_c"]):
            return account_obj.search(
                [
                    ("code", "like", account_mapping[line["concepto_c"]]),
                    ("company_id", "=", journal.company_id.id),
                ],
                limit=1,
            )
        return account_obj.browse()

    @api.model
    def _parse_file(self, data_file):
        n43s = self._check_n43(data_file)
        if not n43s:  # pragma: no cover
            return super()._parse_file(data_file)
        result = []
        for n43 in n43s:
            data = self._parse_single_file_n43(n43)
            if data[2]:
                # We should only add data if there is some transactions.
                # Otherwise we could ignore it.
                result.append(data)
        return result

    def _parse_single_file_n43(self, n43):
        transactions = []
        for group in n43:
            for line in group["lines"]:
                conceptos = []
                for concept_line in line["conceptos"]:
                    conceptos.extend(
                        x.strip() for x in line["conceptos"][concept_line] if x.strip()
                    )
                vals_line = {
                    "payment_ref": " ".join(conceptos)
                    or self._get_n43_ref(line)
                    or "/",
                    "ref": self._get_n43_ref(line),
                    "amount": line["importe"],
                    # inject raw parsed N43 dict for later use, that will be
                    # removed before passing final values to create the record
                    "n43_line": line,
                }
                c = line["conceptos"]
                if c.get("01"):
                    vals_line["partner_name"] = c["01"][0] + c["01"][1]
                transactions.append(vals_line)
        vals_bank_statement = {
            "transactions": transactions,
            "balance_start": n43 and n43[0]["saldo_ini"] or 0.0,
            "balance_end_real": n43 and n43[-1]["saldo_fin"] or 0.0,
        }
        return (
            self._get_currency_iso4217(int(n43[0]["divisa"])),
            n43 and n43[0]["cuenta"] or None,
            [vals_bank_statement],
        )

    def _get_currency_iso4217(self, iso_currency):
        if self.env["res.currency"]._fields.get("numeric_code"):
            # We will use the info from base_currency_iso_4217 if it is installed
            return (
                self.env["res.currency"]
                .search([("numeric_code", "=", iso_currency)])
                .name
            )
        return CURRENCY_ISO4217_MAP.get(iso_currency)

    def _complete_stmts_vals(self, stmts_vals, journal, account_number):
        """Match partner_id if if hasn't been deducted yet."""
        res = super()._complete_stmts_vals(stmts_vals, journal, account_number)
        for st_vals in res:
            for line_vals in st_vals["transactions"]:
                if line_vals.get("n43_line"):
                    n43_line = line_vals.pop("n43_line")
                    if not line_vals.get("partner_id"):
                        line_vals["partner_id"] = self._get_n43_partner(
                            n43_line,
                        ).id
                    line_vals["date"] = fields.Date.to_string(
                        n43_line.get(journal.n43_date_type or "fecha_valor")
                    )
                # This can't be used, as Odoo doesn't present the lines
                # that already have a counterpart account as final
                # verification, making this very counter intuitive to the user
                # line_vals['account_id'] = self._get_n43_account(
                #     line_vals['raw_data'], journal).id
        return res
