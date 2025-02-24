# Copyright 2015 Omar Castiñeira (Comunitea)
# Copyright 2017 Creu Blanca
# Copyright 2023 QubiQ - Jan Tugores (jan.tugores@qubiq.es)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    facturae = fields.Boolean("Factura electrónica", copy=False)
    facturae_version = fields.Selection(
        [("3_2", "3.2"), ("3_2_1", "3.2.1"), ("3_2_2", "3.2.2")]
    )
    facturae_hide_discount = fields.Boolean(
        string="Hide Facturae discount",
        help="The unit price will be recalculated applying the discount",
    )
    organo_gestor = fields.Char(size=10)
    unidad_tramitadora = fields.Char(size=10)
    oficina_contable = fields.Char(size=10)
    organo_proponente = fields.Char("Órgano proponente", size=10)
    attach_invoice_as_annex = fields.Boolean()

    def get_facturae_residence(self):
        if not self.country_id:
            return "E"
        if self.country_id.code == "ES":
            return "R"
        for group in self.country_id.country_group_ids:
            if group.name == "Europe":
                return "U"
        return "E"

    @api.constrains("facturae", "vat", "state_id", "country_id", "street")
    def check_facturae(self):
        for record in self:
            if record.facturae:
                if not record.vat:
                    raise ValidationError(
                        _("Vat must be defined for factura-e enabled partners.")
                    )
                if not record.street:
                    raise ValidationError(
                        _("Street must be defined for factura-e enabled partners.")
                    )
                if not record.country_id:
                    raise ValidationError(
                        _("Country must be defined for factura-e enabled partners.")
                    )
                if record.country_id.code_alpha3 == "ESP":
                    if not record.state_id:
                        raise ValidationError(
                            _("State must be defined for factura-e enabled partners.")
                        )

    @api.model
    def _commercial_fields(self):
        return super()._commercial_fields() + ["facturae"]
