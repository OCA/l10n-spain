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
