# Copyright 2016 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from . import common


class TestL10nEsFacturae321(common.CommonTest):
    def setUp(self):
        super().setUp()
        self.partner.facturae_version = "3_2_2"
        self.fe = "http://www.facturae.gob.es/formato/Versiones/Facturaev3_2_2.xml"
        self.first_check_amount = [
            "190.31000000",
            "190.31000000",
            "190.31000000",
            "39.96510000",
        ]
        self.second_check_amount = [
            "190.31000000",
            "133.22000000",
            "133.22000000",
            "27.97620000",
        ]
        self.refund_check_amount = [
            "-100.00000000",
            "-100.00000000",
            "-100.00000000",
            "-21.00000000",
        ]
        self.refund_check_totals = [
            "-100.00000000",
            "-100.00000000",
            "-21.00000000",
            "-121.00000000",
        ]
        self.hided_discount_check_amount = [
            "133.21700000",
            "133.22000000",
            "133.22000000",
            "27.97620000",
        ]
