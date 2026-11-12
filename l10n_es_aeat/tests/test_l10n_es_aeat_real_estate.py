# Copyright 2025 Netkia - Carlos Sainz-Pardo
# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.exceptions import ValidationError
from odoo.fields import Command
from odoo.tests import Form
from odoo.tools.safe_eval import safe_eval

from ..models.aeat_address_types import AEAT_ADDRESS_TYPES
from .common import TestL10nEsAeatModBase

_logger = logging.getLogger("aeat")


class TestL10nEsAeatRealEstate(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False

    # Referencias catastrales generadas aleatoriamente
    references = {  # noqa: RUF012
        1: "8374992BV4192Q4560EG",
        2: "7466896WH0452Y6611MK",
        3: "5910144GZ3516I1918GW",
        4: "0982928DM2611S1798DJ",
    }

    def _base_vals(self, name="Test RE"):
        return {
            "name": name,
            "partner_id": self.supplier.id,
            "address_type": "CALLE",
            "address": "C/ Prueba",
            "number_type": "NUM",
            "number": 5,
            "city": "Madrid",
            "zip": "28001",
        }

    def test_compute_real_estate_situation(self):
        # Caso 1: Sin referencia → situación 4
        r1 = self.env["l10n.es.aeat.real_estate"].create(
            {
                **self._base_vals("Inmueble 1"),
                "city": "Torrelavega",
                "zip": "39301",
                "state_id": self.env.ref("base.state_es_s").id,  # Cantabria
                "reference": False,
            }
        )
        self.assertEqual(r1.real_estate_situation, "4")

        # Caso 2: Con referencia y código fuera del PV/NA → situación 1
        r2 = self.env["l10n.es.aeat.real_estate"].create(
            {
                **self._base_vals("Inmueble 2"),
                "reference": self.references[1],
                "state_id": self.env.ref("base.state_es_m").id,  # Madrid
            }
        )
        self.assertEqual(r2.real_estate_situation, "1")

        # Caso 3a: Vizcaya (BI) → situación 2
        r3 = self.env["l10n.es.aeat.real_estate"].create(
            {
                **self._base_vals("Inmueble 3"),
                "city": "Bilbao",
                "zip": "48001",
                "reference": self.references[2],
                "state_id": self.env.ref("base.state_es_bi").id,
            }
        )
        self.assertEqual(r3.real_estate_situation, "2")

        # Caso 3b: Guipúzcoa (SS) → situación 2
        r3b = self.env["l10n.es.aeat.real_estate"].create(
            {
                **self._base_vals("Inmueble 3b"),
                "city": "San Sebastián",
                "zip": "20001",
                "reference": self.references[2],
                "state_id": self.env.ref("base.state_es_ss").id,
            }
        )
        self.assertEqual(r3b.real_estate_situation, "2")

        # Caso 3c: Álava (VI) → situación 2
        r3c = self.env["l10n.es.aeat.real_estate"].create(
            {
                **self._base_vals("Inmueble 3c"),
                "city": "Vitoria",
                "zip": "01001",
                "reference": self.references[2],
                "state_id": self.env.ref("base.state_es_vi").id,
            }
        )
        self.assertEqual(r3c.real_estate_situation, "2")

        # Caso 4: Navarra (NA) → situación 3
        r4 = self.env["l10n.es.aeat.real_estate"].create(
            {
                **self._base_vals("Inmueble 4"),
                "city": "Pamplona",
                "zip": "31001",
                "reference": self.references[3],
                "state_id": self.env.ref("base.state_es_na").id,
            }
        )
        self.assertEqual(r4.real_estate_situation, "3")

        # Caso 5: Con referencia pero sin state_id → situación 1
        r5 = self.env["l10n.es.aeat.real_estate"].create(
            {
                **self._base_vals("Inmueble 5"),
                "reference": self.references[1],
            }
        )
        self.assertEqual(r5.real_estate_situation, "1")

    def test_normalize_reference(self):
        model = self.env["l10n.es.aeat.real_estate"]
        self.assertEqual(
            model._normalize_reference("8374992BV4192Q-4560EG"),
            "8374992BV4192Q4560EG",
        )
        self.assertEqual(
            model._normalize_reference("8374 992B V4192Q.4560_EG"),
            "8374992BV4192Q4560EG",
        )
        self.assertEqual(model._normalize_reference("abc"), "ABC")
        self.assertEqual(model._normalize_reference(""), "")
        self.assertEqual(model._normalize_reference(None), "")

    def test_is_valid_reference(self):
        model = self.env["l10n.es.aeat.real_estate"]

        # Referencias válidas
        for ref in self.references.values():
            self.assertTrue(model._is_valid_reference(ref), f"{ref} debería ser válida")

        # Casos inválidos
        self.assertFalse(model._is_valid_reference(None))
        self.assertFalse(model._is_valid_reference(""))
        self.assertFalse(
            model._is_valid_reference("1234567AB1234A0001WL")
        )  # control erróneo
        self.assertFalse(model._is_valid_reference("SHORT"))  # demasiado corta
        self.assertFalse(
            model._is_valid_reference("1234567AB1234A0001OJ!")
        )  # demasiado larga
        self.assertFalse(
            model._is_valid_reference("1234567ab1234a0001oj")
        )  # minúsculas

    def test_check_reference_constraint(self):
        # Referencia válida: no lanza excepción
        rec = self.env["l10n.es.aeat.real_estate"].create(
            {**self._base_vals(), "reference": self.references[1]}
        )
        self.assertEqual(rec.reference, self.references[1])

        # Referencia vacía: permitida
        rec_no_ref = self.env["l10n.es.aeat.real_estate"].create(
            {**self._base_vals("Sin ref"), "reference": False}
        )
        self.assertFalse(rec_no_ref.reference)

        # Referencia con separadores: se normaliza y valida correctamente
        ref_with_sep = self.references[1][:7] + "-" + self.references[1][7:]
        rec_sep = self.env["l10n.es.aeat.real_estate"].create(
            {**self._base_vals("Con sep"), "reference": ref_with_sep}
        )
        self.assertTrue(rec_sep.reference)

        # Referencia inválida: lanza ValidationError
        with self.assertRaises(ValidationError):
            self.env["l10n.es.aeat.real_estate"].create(
                {**self._base_vals("Inválida"), "reference": "1234567AB1234A0001WL"}
            )

    def test_compute_check_ok(self):
        # Sin state_id → check_ok=False
        rec_no_state = self.env["l10n.es.aeat.real_estate"].create(
            self._base_vals("Sin estado")
        )
        self.assertFalse(rec_no_state.check_ok)
        self.assertTrue(rec_no_state.error_text)

        # Con state_id → check_ok=True
        rec_with_state = self.env["l10n.es.aeat.real_estate"].create(
            {
                **self._base_vals("Con estado"),
                "state_id": self.env.ref("base.state_es_m").id,
            }
        )
        self.assertTrue(rec_with_state.check_ok)
        self.assertFalse(rec_with_state.error_text)

    def test_compute_representative_vat(self):
        partner = self.env["res.partner"].create(
            {"name": "Test VAT partner", "vat": "ES00000000T"}
        )
        rec = self.env["l10n.es.aeat.real_estate"].create(
            {**self._base_vals(), "partner_id": partner.id}
        )
        self.assertEqual(rec.representative_vat, "ES00000000T")

        # Al cambiar el NIF del partner se recalcula
        partner.vat = "ES00000001R"
        self.assertEqual(rec.representative_vat, "ES00000001R")

    def test_01_invoice_report_queries_and_groups_by_real_estate(self):
        real_estate = self.env["l10n.es.aeat.real_estate"].create(
            {
                **self._base_vals("Invoice report estate"),
                "partner_id": self.customer.id,
                "state_id": self.env.ref("base.state_es_m").id,
            }
        )
        invoice = self._invoice_sale_create(
            "2024-02-01",
            {
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Real estate invoice line",
                            "account_id": self.accounts["700000"].id,
                            "price_unit": 1000,
                            "quantity": 1,
                            "l10n_es_aeat_real_estate_id": real_estate.id,
                        }
                    )
                ]
            },
        )
        report = self.env["account.invoice.report"]
        domain = [("move_id", "=", invoice.id)]
        self.assertEqual(
            report.search(domain).mapped("l10n_es_aeat_real_estate_id"),
            real_estate,
        )
        self.assertEqual(
            report._read_group(domain, ["l10n_es_aeat_real_estate_id"], ["__count"]),
            [(real_estate, 1)],
        )

    def test_reference_outside_the_dgc_cadastre(self):
        """The Basque Country, Navarre and the foreign countries have their own
        cadastral references, without the control characters of the DGC."""
        foral_reference = "201001000123400001"
        for state_xmlid in ("base.state_es_na", "base.state_es_bi"):
            estate = self.env["l10n.es.aeat.real_estate"].create(
                {
                    **self._base_vals(state_xmlid),
                    "reference": foral_reference,
                    "state_id": self.env.ref(state_xmlid).id,
                }
            )
            self.assertEqual(estate.reference, foral_reference)
        abroad = self.env["l10n.es.aeat.real_estate"].create(
            {
                **self._base_vals("Abroad"),
                "reference": "FR-75056-000AB-0123",
                "country_id": self.env.ref("base.fr").id,
            }
        )
        self.assertTrue(abroad.reference)
        # Moved to the territory of the DGC, the reference is checked again
        with self.assertRaises(ValidationError):
            estate.state_id = self.env.ref("base.state_es_m")

    def test_address_types(self):
        """One name per street type, kept out of the translations because the
        names are already given in the co-official languages."""
        keys = [key for key, _name in AEAT_ADDRESS_TYPES]
        self.assertEqual(len(keys), len(set(keys)))
        field = self.env["ir.model.fields"]._get(
            "l10n.es.aeat.real_estate", "address_type"
        )
        self.assertFalse(field.selection_ids)
        estate = self.env["l10n.es.aeat.real_estate"].create(
            {**self._base_vals(), "address_type": "APDRO"}
        )
        self.assertEqual(estate.address_type, "APDRO")

    def test_real_estate_owned_by_another_company(self):
        """A real estate owned by another company of the database is not owned
        by the company declaring it, and a customer invoice line of the latter
        only offers the real estates of the company itself."""
        other_company = (
            self.env["res.company"].sudo().create({"name": "Sister company"})
        )
        estate = self.env["l10n.es.aeat.real_estate"].create(
            {
                **self._base_vals("Premises of the sister company"),
                "company_id": self.company.id,
                "partner_id": other_company.partner_id.id,
            }
        )
        own_estate = self.env["l10n.es.aeat.real_estate"].create(
            {
                **self._base_vals("Premises of the company"),
                "company_id": self.company.id,
                "partner_id": self.company.partner_id.id,
            }
        )
        self.assertFalse(estate.owned_by_company)
        RealEstate = self.env["l10n.es.aeat.real_estate"]
        self.assertFalse(
            RealEstate.search([("id", "=", estate.id), ("owned_by_company", "=", True)])
        )
        self.assertEqual(
            RealEstate.search(
                [("id", "=", estate.id), ("owned_by_company", "=", False)]
            ),
            estate,
        )
        # The dropdown of the line searches with the domain of the field
        invoice_form = Form(
            self.env["account.move"].with_context(default_move_type="out_invoice")
        )
        invoice_form.partner_id = self.customer
        with invoice_form.invoice_line_ids.new() as line_form:
            line_form.name = "Rent"
            line_form.price_unit = 100
        line = invoice_form.save().invoice_line_ids
        domain = safe_eval(
            line._fields["l10n_es_aeat_real_estate_id"].domain,
            {"company_id": line.company_id.id, "partner_id": line.partner_id.id},
        )
        offered = RealEstate.browse(
            [rec_id for rec_id, _name in RealEstate.name_search("Premises", domain)]
        )
        self.assertEqual(offered, own_estate)

    def test_real_estates_of_the_invoice_lines(self):
        """The lines offer the real estates of the partner of the invoice and
        the ones of the company, like the premises it leases to a customer."""
        company_estate = self.env["l10n.es.aeat.real_estate"].create(
            {
                **self._base_vals("Leased premises"),
                "company_id": self.company.id,
                "partner_id": self.company.partner_id.id,
            }
        )
        supplier_estate = self.env["l10n.es.aeat.real_estate"].create(
            {**self._base_vals("Rented office"), "company_id": self.company.id}
        )
        self.assertTrue(company_estate.owned_by_company)
        self.assertFalse(supplier_estate.owned_by_company)
        domain = (
            self.env["account.move.line"]._fields["l10n_es_aeat_real_estate_id"].domain
        )
        estates = company_estate | supplier_estate
        for partner, expected in (
            (self.customer, company_estate),
            (self.supplier, estates),
        ):
            self.assertEqual(
                self.env["l10n.es.aeat.real_estate"].search(
                    safe_eval(
                        domain,
                        {"company_id": self.company.id, "partner_id": partner.id},
                    )
                    + [("id", "in", estates.ids)]
                ),
                expected,
                partner.name,
            )
