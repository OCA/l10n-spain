from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    vat = fields.Char(
        readonly=False,
        store=True,
        compute="_compute_vat",
    )
    aeat_identification_type = fields.Selection(
        readonly=False,
        store=True,
        compute="_compute_aeat_identification_type",
    )
    aeat_identification = fields.Char(
        readonly=False,
        store=True,
        compute="_compute_aeat_identification",
    )

    @api.depends(
        "id_numbers",
        "id_numbers.category_id",
        "id_numbers.category_id.aeat_identification_type",
    )
    def _compute_aeat_identification_type(self):
        if hasattr(super(), "_compute_aeat_identification_type"):
            super()._compute_aeat_identification_type()
        for record in self:
            # Passport ("03"), Residential cert. ("04") and Another document ("05")
            # are setted in aeat identificacion type.
            # NIF/VAT ("02") and Official document from de original country ("04")
            # are setted in partner vat field compute
            document = record.id_numbers.filtered(
                lambda i: i.category_id.aeat_identification_type in ["03", "05", "06"]
            )
            if document and not record.vat:
                record.aeat_identification_type = document[
                    0
                ].category_id.aeat_identification_type
            elif not record.aeat_identification_type or record.vat:
                record.aeat_identification_type = False

    @api.depends("id_numbers", "id_numbers.name")
    def _compute_aeat_identification(self):
        if hasattr(super(), "_compute_aeat_identification"):
            super()._compute_aeat_identification()
        for record in self:
            document = record.id_numbers.filtered(
                lambda i: i.category_id.aeat_identification_type in ["03", "05", "06"]
            )
            if document:
                record.aeat_identification = document[0].name
            elif not record.aeat_identification:
                record.aeat_identification = False

    @api.depends("id_numbers", "id_numbers.name")
    def _compute_vat(self):
        if hasattr(super(), "_compute_vat"):
            super()._compute_vat()
        for record in self:
            if not record.parent_id:
                document_vats = record.id_numbers.filtered(
                    lambda i: i.category_id.aeat_identification_type in ["02", "04"]
                )
                if document_vats and not record.vat:
                    record.vat = document_vats[0].name
                elif not record.vat:
                    record.vat = False
