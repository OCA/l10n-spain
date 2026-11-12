# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.tests.common import new_test_user


class DecaCommon:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                tracking_disable=True,
                no_reset_password=True,
                lang="en_US",
            )
        )
        # Control both core and optional logistics-unit settings in rollback fixtures.
        parameters = cls.env["ir.config_parameter"]
        parameters.set_param("product.weight_in_lbs", "0")
        parameters.set_param(
            "product_default_weight_uom_id", cls.env.ref("uom.product_uom_kgm").id
        )
        cls.company = cls.env["res.company"].create(
            {"name": "DECA Test Company", "vat": "ES12345678Z", "city": "Madrid"}
        )
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=cls.company.ids)
        )
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.company.id)], limit=1
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "DECA Customer",
                "vat": "ES12345678Z",
                "street": "Customer Street 10",
                "city": "Barcelona",
                "lang": "en_US",
            }
        )
        cls.carrier_contact = cls.env["res.partner"].create(
            {
                "name": "DECA Carrier",
                "vat": "ES12345678Z",
                "street": "Carrier Street 20",
                "lang": "en_US",
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "DECA Test Cargo", "type": "consu", "weight": 2.5}
        )
        cls.picking_type_out = cls.warehouse.out_type_id
        cls.location_customer = cls.env.ref("stock.stock_location_customers")
        cls.location_stock = cls.warehouse.lot_stock_id
        cls.picking = cls._make_picking()
        cls.move = cls.picking.move_ids
        cls.stock_user = new_test_user(
            cls.env,
            login="deca_inventory",
            groups="stock.group_stock_user",
            company_id=cls.company.id,
            company_ids=[Command.set(cls.company.ids)],
        )
        cls.internal_user = new_test_user(
            cls.env,
            login="deca_internal",
            groups="base.group_user",
            company_id=cls.company.id,
            company_ids=[Command.set(cls.company.ids)],
        )

    @classmethod
    def _make_picking(cls, incoming=False):
        picking_type = cls.warehouse.in_type_id if incoming else cls.picking_type_out
        picking_type.l10n_es_deca_enabled = incoming
        source = (
            cls.env.ref("stock.stock_location_suppliers")
            if incoming
            else cls.location_stock
        )
        destination = cls.location_stock if incoming else cls.location_customer
        return cls.env["stock.picking"].create(
            {
                "partner_id": cls.partner.id,
                "picking_type_id": picking_type.id,
                "location_id": source.id,
                "location_dest_id": destination.id,
                "tractor_license_plate": "1111AAA",
                "trailer_license_plate": "R1111BBB",
                "special_authorization": "AUTH-123",
                "carrier_contact_id": cls.carrier_contact.id,
                "move_ids": [
                    Command.create(
                        {
                            "name": "DECA Cargo",
                            "product_id": cls.product.id,
                            "product_uom_qty": 10,
                            "product_uom": cls.product.uom_id.id,
                            "location_id": source.id,
                            "location_dest_id": destination.id,
                        }
                    )
                ],
            }
        )

    def _pdf(self, pickings=None):
        pickings = self.picking if pickings is None else pickings
        return (
            self.env["ir.actions.report"]
            .with_context(force_report_rendering=True)
            ._render_qweb_pdf("l10n_es_deca_oca.report_deca", pickings.ids)
        )
