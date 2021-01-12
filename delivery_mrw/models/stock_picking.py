# Copyright 2021 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    has_mrw_carrier = fields.Boolean(
        string='Has MRW carrier', compute='_get_has_mrw_carrier')

    def _get_has_mrw_carrier(self):
        for picking in self:
            mrw_carrier = False
            if picking.carrier_id\
                    and picking.carrier_id.delivery_type == 'mrw':
                mrw_carrier = True
            picking.has_mrw_carrier = mrw_carrier

    def mrw_get_label(self):
        """Get MRW Label for this picking expedition"""
        self.ensure_one()
        if self.delivery_type != 'mrw':
            return
        label_response = self.carrier_id.mrw_request_label(
            self.tracking_number_ref)
        pdf_content = label_response.get("label_file")
        label_name = "mrw_{}.pdf".format(self.tracking_number_ref)
        self.message_post(
            body=(_("MRW label for %s") % self.tracking_number_ref),
            attachments=[(label_name, pdf_content)],
        )
