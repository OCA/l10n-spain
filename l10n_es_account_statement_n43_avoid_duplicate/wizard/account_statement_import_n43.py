import base64
import logging

from odoo import _, models
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)


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

    def import_file_button(self):
        self.ensure_one()
        result = {
            "statement_ids": [],
            "notifications": [],
        }
        logger.info("Start to import bank statement file %s", self.statement_filename)
        file_data = base64.b64decode(self.statement_file)
        self.import_single_file(file_data, result)
        logger.debug("result=%s", result)
        if not result["statement_ids"]:
            raise UserError(
                _(
                    "You have already imported this file, or this file "
                    "only contains already imported transactions."
                )
            )
        self.env["ir.attachment"].create(self._prepare_create_attachment(result))
        lines = self.env["account.bank.statement.line"].search(
            [("statement_id", "in", result["statement_ids"])]
        )
        duplicated_line_ids = []
        for line_id in lines:
            transaction_hash = line_id.transaction_hash
            same_line_id = (
                self.env["account.bank.statement.line"].search(
                    [
                        ("transaction_hash", "=", transaction_hash),
                    ]
                )
                - line_id
            )
            if same_line_id:
                duplicated_line_ids.append(line_id.id)
        statement_id = lines.statement_id
        if duplicated_line_ids:
            action = (
                self.env.ref(
                    "l10n_es_account_statement_n43_avoid_duplicate.duplicated_n43_action"
                )
                .sudo()
                .read()[0]
            )
            action["context"] = {
                "default_line_ids": duplicated_line_ids,
                "default_statement_id": statement_id.id,
            }
        else:
            if self.env.context.get("return_regular_interface_action"):
                action = (
                    self.env.ref("account.action_bank_statement_tree")
                    .sudo()
                    .read([])[0]
                )
                if len(result["statement_ids"]) == 1:
                    action.update(
                        {
                            "view_mode": "form,tree",
                            "views": False,
                            "res_id": result["statement_ids"][0],
                        }
                    )
                else:
                    action["domain"] = [("id", "in", result["statement_ids"])]
            else:
                # dispatch to reconciliation interface
                lines = self.env["account.bank.statement.line"].search(
                    [("statement_id", "in", result["statement_ids"])]
                )
                action = {
                    "type": "ir.actions.client",
                    "tag": "bank_statement_reconciliation_view",
                    "context": {
                        "statement_line_ids": lines.ids,
                        "company_ids": self.env.user.company_ids.ids,
                        "notifications": result["notifications"],
                    },
                }
        return action
