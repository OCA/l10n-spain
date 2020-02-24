# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import models, exceptions, _
import base64


class AccountInvoiceIntegrationMethod(models.Model):
    _inherit = "account.invoice.integration.method"

    # Default values for integration. It could be extended
    def integration_values(self, invoice):
        res = super(AccountInvoiceIntegrationMethod, self).integration_values(
            invoice
        )
        if self.code == 'eFACT':
            if not invoice.company_id.facturae_cert:
                raise exceptions.UserError(
                    _('Certificate must be added for company'))
            if not invoice.company_id.facturae_cert_password:
                raise exceptions.UserError(
                    _('Certificate password must be added for company'))
            invoice_file, file_name = invoice.get_facturae(True)
            attachment = self.env['ir.attachment'].create({
                'name': file_name,
                'datas': base64.b64encode(invoice_file),
                'datas_fname': file_name,
                'res_model': 'account.invoice',
                'res_id': invoice.id,
                'mimetype': 'application/xml'
            })
            res['attachment_id'] = attachment.id
        return res
