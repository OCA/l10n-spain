# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models
import base64


class CTTExpressManifestWizard(models.TransientModel):
    _name = "cttexpress.manifest.wizard"
    _description = "Get the CTT Express Manifest for the given date range"

    process_code = fields.Selection(
        selection=[("MAGENTO", "Magento"), ("PRESTASHOP", "Prestashop")],
        default="MAGENTO",
        required=True,
    )
    document_type = fields.Selection(
        selection=[("XLSX", "Excel"), ("PDF", "PDF")],
        string="Format",
        default="XLSX",
        required=True,
    )
    from_date = fields.Date(
        required=True, default=fields.Date.context_today
    )
    to_date = fields.Date(
        required=True, default=fields.Date.context_today
    )
    carrier_ids = fields.Many2many(
        string="Filter accounts",
        comodel_name="delivery.carrier",
        domain=[("delivery_type", "=", "cttexpress")],
        help="Leave empty to gather all the CTT account manifests",
    )
    state = fields.Selection(
        selection=[("new", "new"), ("done", "done")],
        default="new",
        readonly=True,
    )
    attachment_ids = fields.Many2many(
        comodel_name="ir.attachment",
        readonly=True,
        string="Manifests"
    )

    def get_manifest(self):
        """List of shippings for the given dates as CTT provides them"""
        carriers = self.carrier_ids or self.env["delivery.carrier"].search(
            [("delivery_type", "=", "cttexpress")]
        )
        # Avoid getting repeated manifests. Carriers with different service
        # configuration would produce the same manifest.
        unique_accounts = set([
            (
                c.cttexpress_customer,
                c.cttexpress_contract,
                c.cttexpress_agency
            )
            for c in carriers
        ])
        filtered_carriers = self.env["delivery.carrier"]
        for customer, contract, agency in unique_accounts:
            filtered_carriers += fields.first(carriers.filtered(
                lambda x: x.cttexpress_customer == customer
                and x.cttexpress_contract == contract
                and x.cttexpress_agency == agency
            ))
        for carrier in filtered_carriers:
            ctt_request = carrier._ctt_request()
            from_date = fields.Date.to_string(self.from_date)
            to_date = fields.Date.to_string(self.to_date)
            error, manifest = ctt_request.report_shipping(
                self.process_code,
                self.document_type,
                from_date,
                to_date
            )
            carrier._ctt_check_error(error)
            carrier._ctt_log_request(ctt_request)
            for _filename, file in manifest:
                filename = "{}{}{}-{}-{}.{}".format(
                    carrier.cttexpress_customer,
                    carrier.cttexpress_contract,
                    carrier.cttexpress_agency,
                    from_date.replace("-", ""),
                    to_date.replace("-", ""),
                    self.document_type.lower()
                )
                self.attachment_ids += self.env["ir.attachment"].create({
                    "datas": base64.b64encode(file),
                    "name": filename,
                    "datas_fname": filename,
                    "res.model": self._name,
                    "res_id": self.id,
                    "type": "binary",
                })
        self.state = "done"
        return dict(
            self.env["ir.actions.act_window"].for_xml_id(
                "delivery_cttexpress",
                "action_delivery_cttexpress_manifest_wizard"
            ),
            res_id=self.id
        )
