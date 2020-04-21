# Copyright 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


import base64

from odoo import _, fields, models


class AccountMoveIntegrationMethod(models.Model):
    _name = "account.move.integration.method"
    _description = "Integration method for moves"

    name = fields.Char()
    code = fields.Char(readonly=True)
    sequence_id = fields.Many2one(
        comodel_name="ir.sequence", readonly=True, required=True
    )

    # Default values for integration. It could be extended
    def integration_values(self, move):
        res = {"method_id": self.id, "move_id": move.id}
        if move.partner_id.attach_invoice_as_annex:
            action = self.env.ref("account.account_invoices")
            content, content_type = action.render(move.ids)
            fname = _("Invoice %s") % move.number
            mimetype = False
            if content_type == "pdf":
                mimetype = "application/pdf"
            if content_type == "xls":
                mimetype = "application/vnd.ms-excel"
            if content_type == "xlsx":
                mimetype = (
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                )
            if content_type == "csv":
                mimetype = "text/csv"
            if content_type == "xml":
                mimetype = "application/xml"
            res["attachment_ids"].append(
                (
                    0,
                    0,
                    {
                        "name": fname,
                        "datas": base64.b64encode(content),
                        "datas_fname": fname,
                        "res_model": "account.move",
                        "res_id": move.id,
                        "mimetype": mimetype,
                    },
                )
            )
        return res

    def create_integration(self, move):
        self.ensure_one()
        self.env["account.move.integration"].create(self.integration_values(move))
