# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from lxml import etree

from odoo import fields, models

from odoo.addons.l10n_es_ticketbai_api.ticketbai.xml_schema import TicketBaiSchema


class TicketBAIInvoice(models.Model):
    _inherit = "tbai.invoice"

    pos_order_id = fields.Many2one(comodel_name="pos.order")

    def send(self, **kwargs):
        self.ensure_one()
        if TicketBaiSchema.TicketBai.value == self.schema and self.pos_order_id:
            res = super().send(pos_order_id=self.pos_order_id.id, **kwargs)
        else:
            res = super().send(**kwargs)
        return res

    def build_tbai_simplified_invoice(self):
        self.ensure_one()
        if self.schema == TicketBaiSchema.TicketBai.value:
            self.previous_tbai_invoice_id = (
                self.pos_order_id.config_id.tbai_last_invoice_id
            )
        root, signature_value = self.get_tbai_xml_signed_and_signature_value()
        root_str = etree.tostring(root, xml_declaration=True, encoding="utf-8")
        self.datas = base64.b64encode(root_str)
        self.datas_fname = "%s.xsig" % self.name.replace("/", "-")
        self.file_size = len(self.datas)
        self.signature_value = signature_value
        self.mark_as_pending()
        if self.schema == TicketBaiSchema.TicketBai.value:
            self.pos_order_id.config_id.tbai_last_invoice_id = self
