from odoo import models


class AccountStatementImport(models.TransientModel):
    _inherit = "account.statement.import"

    def _process_record_22(self, line):
        res = super()._process_record_22(line)
        res["transaction_raw_register"] = line
        return res

    def _process_record_23(self, st_line, line):
        res = super()._process_record_23(st_line, line)
        res["transaction_raw_register"] += line
        return res

    def _complete_stmts_vals(self, stmts_vals, journal, account_number):
        for st_vals in stmts_vals:
            for line_vals in st_vals["transactions"]:
                line_vals["transaction_raw_register"] = line_vals.get("n43_line").get(
                    "transaction_raw_register"
                )
        res = super()._complete_stmts_vals(stmts_vals, journal, account_number)
        return res
