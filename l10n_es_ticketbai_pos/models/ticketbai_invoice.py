# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from lxml import etree
from odoo.addons.l10n_es_ticketbai_api.ticketbai.xml_schema import TicketBaiSchema
from odoo import models, fields, api


class TicketBAIInvoice(models.Model):
    _inherit = 'tbai.invoice'

    pos_order_id = fields.Many2one(comodel_name='pos.order')

    @api.multi
    def send(self, **kwargs):
        self.ensure_one()
        if TicketBaiSchema.TicketBai.value == self.schema and self.pos_order_id:
            res = super().send(pos_order_id=self.pos_order_id.id, **kwargs)
        else:
            res = super().send(**kwargs)
        return res

    @api.multi
    def cancel_and_recreate(self):
        super().cancel_and_recreate()
        for record in self.sudo():
            if TicketBaiSchema.TicketBai.value == record.schema and record.pos_order_id:
                record.pos_order_id._tbai_build_invoice()

    def build_tbai_simplified_invoice(self):
        self.ensure_one()
        if self.schema == TicketBaiSchema.TicketBai.value:
            self.previous_tbai_invoice_id = \
                self.pos_order_id.config_id.tbai_last_invoice_id
        root, signature_value = self.get_tbai_xml_signed_and_signature_value()
        root_str = etree.tostring(root, xml_declaration=True, encoding='utf-8')
        self.datas = base64.b64encode(root_str)
        self.datas_fname = "%s.xsig" % self.name.replace('/', '-')
        self.file_size = len(self.datas)
        self.signature_value = signature_value
        self.mark_as_pending()
        if self.schema == TicketBaiSchema.TicketBai.value:
            self.pos_order_id.config_id.tbai_last_invoice_id = self

    @api.model
    def mark_chain_as_error(self, invoice_to_error):
        # Restore last invoice successfully sent
        if invoice_to_error.pos_order_id:
            if TicketBaiSchema.TicketBai.value == invoice_to_error.schema:
                invoice_to_error.pos_order_id.config_id.tbai_last_invoice_id = \
                    invoice_to_error.previous_tbai_invoice_id
            while invoice_to_error:
                invoice_to_error.error()
                invoice_to_error = self.search([
                    ('previous_tbai_invoice_id', '=', invoice_to_error.id)
                ])
        else:
            super().mark_chain_as_error(invoice_to_error)
