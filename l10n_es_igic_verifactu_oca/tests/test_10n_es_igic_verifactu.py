# Copyright 2025 Binhex - Christian Ramos
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from odoo.addons.l10n_es_verifactu_oca.tests.test_10n_es_verifactu import (
    TestL10nEsAeatVerifactu,
)

from .common import TestVerifactuIgicCommon


class TestL10nEsAeatVerifactuIgic(TestVerifactuIgicCommon):
    def test_verifactu_hash_code(self):
        TestL10nEsAeatVerifactu.test_verifactu_hash_code(self)

    def _create_and_test_invoice_verifactu_dict(
        self, name, inv_type, lines, extra_vals, module=None
    ):
        return TestL10nEsAeatVerifactu._create_and_test_invoice_verifactu_dict(
            self, name, inv_type, lines, extra_vals, module
        )

    def test_get_verifactu_invoice_data(self):
        mapping = [
            (
                "TEST001",
                "out_invoice",
                [(100, ["igic_r_3"]), (200, ["igic_r_7"])],
                {
                    "fiscal_position_id": self.fp_nacional.id,
                    "verifactu_registration_key": self.fp_registration_key_01.id,
                    "verifactu_registration_date": "2026-01-01 19:20:30",
                },
            ),
            (
                "TEST002",
                "out_refund",
                [(100, ["igic_r_3"]), (100, ["igic_r_3"]), (200, ["igic_r_7"])],
                {
                    "fiscal_position_id": self.fp_nacional.id,
                    "verifactu_registration_key": self.fp_registration_key_01.id,
                    "verifactu_registration_date": "2026-01-01 19:20:30",
                },
            ),
        ]
        for name, inv_type, lines, extra_vals in mapping:
            self._create_and_test_invoice_verifactu_dict(
                name, inv_type, lines, extra_vals, "l10n_es_igic_verifactu_oca"
            )
        return

    def _compare_verifactu_dict(
        self, json_file, name, inv_type, lines, extra_vals=None, module=None
    ):
        return TestL10nEsAeatVerifactu._compare_verifactu_dict(
            self, json_file, name, inv_type, lines, extra_vals, module
        )

    def test_verifactu_start_date(self):
        TestL10nEsAeatVerifactu.test_verifactu_start_date(self)
