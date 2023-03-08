# Copyright 2022 CreuBlanca
# Copyright 2022 Eric Antones <eantones@nuobit.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

import logging

from .test_l10n_es_aeat_mod_base import TestL10nEsAeatModBase

_logger = logging.getLogger("aeat")


class TestL10nEsAeatTaxInfo(TestL10nEsAeatModBase):
    taxes_sale = {
        # tax code: (base, tax_amount)
        "S_IVA21B": (1000, 0),
    }

    def test_tax_info_21B(self):
        invoice = self._invoice_sale_create("2018-02-01", {})
        tax_info = invoice._get_aeat_tax_info()
        tax = self._get_taxes("S_IVA21B")[0]
        self.assertEqual(tax_info[tax]["base"], 1000)
        self.assertEqual(tax_info[tax]["amount"], 210)

    def test_tax_info_refund_21B(self):
        invoice = self._invoice_sale_create("2018-02-01", {})
        refund = invoice._reverse_moves()
        tax_info = refund._get_aeat_tax_info()
        tax = self._get_taxes("S_IVA21B")[0]
        self.assertEqual(tax_info[tax]["base"], -1000)
        self.assertEqual(tax_info[tax]["amount"], -210)


class TestL10nEsAeatTaxInfoGroup(TestL10nEsAeatModBase):
    taxes_sale = {
        # tax code: (base, tax_amount)
        "S_IVAG1021B": (1000, 0),
    }

    @classmethod
    def _chart_of_accounts_create(cls):
        cls.env["account.tax.template"]._load_records(
            [
                {
                    "xml_id": "l10n_es.account_tax_template_s_ivag1021b",
                    "noupdate": True,
                    "values": {
                        "type_tax_use": "sale",
                        "name": "Grupo IVA 10%/21% (Bienes)",
                        "chart_template_id": cls.env.ref(
                            "l10n_es.account_chart_template_common"
                        ).id,
                        "amount_type": "group",
                        "children_tax_ids": [
                            (
                                6,
                                0,
                                [
                                    cls.env.ref(
                                        "l10n_es.account_tax_template_s_iva10b"
                                    ).id,
                                    cls.env.ref(
                                        "l10n_es.account_tax_template_s_iva21b"
                                    ).id,
                                ],
                            )
                        ],
                    },
                }
            ]
        )
        return super()._chart_of_accounts_create()

    def test_tax_info_1021B(self):
        invoice = self._invoice_sale_create("2018-02-01", {})
        tax_info = invoice._get_aeat_tax_info()
        tax10 = self._get_taxes("S_IVA10B")[0]
        tax21 = self._get_taxes("S_IVA21B")[0]
        self.assertEqual(tax_info[tax10]["base"], 1000)
        self.assertEqual(tax_info[tax10]["amount"], 100)
        self.assertEqual(tax_info[tax21]["base"], 1000)
        self.assertEqual(tax_info[tax21]["amount"], 210)

    def test_tax_info_refund_1021B(self):
        invoice = self._invoice_sale_create("2018-02-01", {})
        refund = invoice._reverse_moves()
        tax_info = refund._get_aeat_tax_info()
        tax10 = self._get_taxes("S_IVA10B")[0]
        tax21 = self._get_taxes("S_IVA21B")[0]
        self.assertEqual(tax_info[tax10]["base"], -1000)
        self.assertEqual(tax_info[tax10]["amount"], -100)
        self.assertEqual(tax_info[tax21]["base"], -1000)
        self.assertEqual(tax_info[tax21]["amount"], -210)
