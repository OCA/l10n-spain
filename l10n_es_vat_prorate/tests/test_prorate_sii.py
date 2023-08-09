from datetime import date

from odoo.tests.common import tagged

from odoo.addons.l10n_es_aeat_sii_oca.tests import test_l10n_es_aeat_sii


@tagged("-at_install", "post_install")
class TestSIIVatProrate(test_l10n_es_aeat_sii.TestL10nEsAeatSiiBase):
    @classmethod
    def setUpClass(cls):
        try:
            super().setUpClass()
        except Exception:
            cls.skipTest(cls, "l10n_es_aeat_sii_oca seems not installed")
        cls.company.write(
            {
                "with_vat_prorate": True,
                "vat_prorate_ids": [
                    (0, 0, {"date": date(2020, 1, 1), "vat_prorate": 20}),
                    (0, 0, {"date": date(2021, 1, 1), "vat_prorate": 10}),
                ],
            }
        )
        # Make sure the currency rate 1.2
        cls.usd = cls.env.ref("base.USD")
        cls.usd.rate_ids.unlink()
        cls.usd.rate_ids.create(
            {"name": "2000-01-01", "rate": 1.2, "currency_id": cls.usd.id}
        )

    def test_get_invoice_data(self):
        mapping = [
            ("out_invoice", [(100, ["s_iva10b"]), (200, ["s_iva21s"])], {}),
            ("out_invoice", [(100, ["s_iva10b"]), (200, ["s_iva0_ns"])], {}),
            (
                "out_invoice",
                [(100, ["s_iva10b", "s_req014"]), (200, ["s_iva21s", "s_req52"])],
                {},
            ),
            (
                "out_refund",
                [(100, ["s_iva10b"]), (100, ["s_iva10b"]), (200, ["s_iva21s"])],
                {},
            ),
            ("out_invoice", [(100, ["s_iva0_sp_i"]), (200, ["s_iva0_ic"])], {}),
            ("out_refund", [(100, ["s_iva0_sp_i"]), (200, ["s_iva0_ic"])], {}),
            ("out_invoice", [(100, ["s_iva_e"]), (200, ["s_iva0_e"])], {}),
            ("out_refund", [(100, ["s_iva_e"]), (200, ["s_iva0_e"])], {}),
            (
                "in_invoice",
                [(100, ["p_iva10_bc", "p_irpf19"]), (200, ["p_iva21_sc", "p_irpf19"])],
                {
                    "ref": "sup0001",
                    "date": "2020-02-01",
                    "sii_account_registration_date": "2020-10-01",
                },
            ),
            (
                "in_refund",
                [(100, ["p_iva10_bc"])],
                {"ref": "sup0002", "sii_account_registration_date": "2020-10-01"},
            ),
            (
                "in_invoice",
                [(100, ["p_iva10_bc", "p_req014"]), (200, ["p_iva21_sc", "p_req52"])],
                {"ref": "sup0003", "sii_account_registration_date": "2020-10-01"},
            ),
            (
                "in_invoice",
                [(100, ["p_iva21_sp_ex"])],
                {"ref": "sup0004", "sii_account_registration_date": "2020-10-01"},
            ),
            (
                "in_invoice",
                [(100, ["p_iva0_ns"]), (200, ["p_iva10_bc"])],
                {"ref": "sup0005", "sii_account_registration_date": "2020-10-01"},
            ),
            # Out invoice with currency
            ("out_invoice", [(100, ["s_iva10b"])], {"currency_id": self.usd.id}),
            # Out invoice with currency and with not included in total amount
            (
                "out_invoice",
                [(100, ["s_iva10b", "s_irpf1"])],
                {"currency_id": self.usd.id},
            ),
            # In invoice with currency
            (
                "in_invoice",
                [(100, ["p_iva10_bc"])],
                {
                    "ref": "sup0006",
                    "sii_account_registration_date": "2020-10-01",
                    "currency_id": self.usd.id,
                },
            ),
            # In invoice with currency and with not included in total amount
            (
                "in_invoice",
                [(100, ["p_iva10_bc", "p_irpf1"])],
                {
                    "ref": "sup0007",
                    "sii_account_registration_date": "2020-10-01",
                    "currency_id": self.usd.id,
                },
            ),
            # Intra-community supplier refund with ImporteTotal with "one side"
            (
                "in_refund",
                [(100, ["p_iva21_sp_in"])],
                {"ref": "sup0008", "sii_account_registration_date": "2020-10-01"},
            ),
        ]
        for inv_type, lines, extra_vals in mapping:
            self._create_and_test_invoice_sii_dict(
                inv_type, lines, extra_vals, module="l10n_es_vat_prorate"
            )
        return
