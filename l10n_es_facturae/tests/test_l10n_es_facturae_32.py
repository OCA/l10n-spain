# Copyright 2016 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from .common import CommonTest


class TestL10nEsFacturae(CommonTest):
    def setUp(self):
        super().setUp()
        self.fe = "http://www.facturae.es/Facturae/2009/v3.2/Facturae"
        self.first_check_amount = ["190.310000", "190.310000", "190.31", "39.97"]
        self.second_check_amount = [
            "190.310000",
            "133.220000",
            "133.22",
            "27.98",
            "57.090000",
        ]
        self.refund_check_amount = ["-100.000000", "-100.000000", "-100.00", "-21.00"]
        self.refund_check_totals = ["-100.00", "-100.00", "-21.00", "-121.00"]
        self.hided_discount_check_amount = [
            "133.217000",
            "133.220000",
            "133.22",
            "27.98",
        ]
