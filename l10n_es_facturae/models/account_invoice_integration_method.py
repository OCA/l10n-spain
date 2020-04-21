# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import models, fields, _
import base64


class AccountInvoiceIntegrationMethod(models.Model):
    _name = "account.invoice.integration.method"
    _description = 'Integration method for invoices'

    name = fields.Char()
    code = fields.Char(readonly=True)
    sequence_id = fields.Many2one(
        comodel_name='ir.sequence',
        readonly=True,
        required=True
    )

    # Default values for integration. It could be extended
    def integration_values(self, invoice):
        res = {
            'method_id': self.id,
            'invoice_id': invoice.id,
            'attachment_ids': []
        }

        if invoice.partner_id.attach_invoice_as_annex:
            action = self.env.ref('account.account_invoices')
            content, content_type = action.render(invoice.ids)
            fname = _("Invoice %s") % invoice.number
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
            res['attachment_ids'].append(
                (0, 0, {
                    "name": fname,
                    "datas": base64.b64encode(content),
                    "datas_fname": fname,
                    'res_model': 'account.invoice',
                    'res_id': invoice.id,
                    "mimetype": mimetype,
                })
            )
        return res

    def create_integration(self, invoice):
        self.ensure_one()
        self.env['account.invoice.integration'].create(
            self.integration_values(invoice)
        )
