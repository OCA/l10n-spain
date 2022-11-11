# © 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

import logging

from .test_l10n_es_aeat_mod_base import TestL10nEsAeatModBase

_logger = logging.getLogger("aeat")


class TestL10nEsAeatModBase(TestL10nEsAeatModBase):
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
