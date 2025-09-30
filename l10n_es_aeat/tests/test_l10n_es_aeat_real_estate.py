# Copyright 2025 Netkia - Carlos Sainz-Pardo
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from odoo.exceptions import ValidationError

from .test_l10n_es_aeat_mod_base import TestL10nEsAeatModBase

_logger = logging.getLogger("aeat")


class TestL10nEsAeatRealEstate(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False

    # Referencias catastrales generadas aleatoriamente
    references = {
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
        # Sin state_code → check_ok=False
        rec_no_state = self.env["l10n.es.aeat.real_estate"].create(
            self._base_vals("Sin estado")
        )
        self.assertFalse(rec_no_state.check_ok)
        self.assertTrue(rec_no_state.error_text)

        # Con state_code → check_ok=True
        rec_with_state = self.env["l10n.es.aeat.real_estate"].create(
            {
                **self._base_vals("Con estado"),
                "state_id": self.env.ref("base.state_es_m").id,
                "state_code": "28",
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
