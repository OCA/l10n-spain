# © 2022 Digital5 SL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import odoo


def migrate(cr, version):
    if not version:
        return
    env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
    tbai_invoice = env["tbai.invoice"]
    tbai_journals = env["account.journal"].search([("tbai_send_invoice", "=", True)])
    for tbai_journal in tbai_journals:
        tbai_invoice_sent = tbai_invoice.search(
            [("invoice_id.journal_id", "=", tbai_journal.id), ("state", "=", "sent")],
            order="operation_date asc",
            limit=1,
        )
        if tbai_invoice_sent:
            tbai_journal.write(
                {
                    "tbai_active_date": tbai_invoice_sent.invoice_id.date
                    or tbai_invoice_sent.invoice_id.invoice_date
                }
            )
