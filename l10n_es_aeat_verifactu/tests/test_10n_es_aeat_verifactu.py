# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from hashlib import sha256

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_certificate import (
    TestL10nEsAeatCertificateBase,
)
from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)


class TestL10nEsAeatSiiBase(TestL10nEsAeatModBase, TestL10nEsAeatCertificateBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_verifactu_hash_code(self):
        # based on AEAT Verifactu documentation
        # https://www.agenciatributaria.es/static_files/AEAT_Desarrolladores/EEDD/IVA/VERI-FACTU/Veri-Factu_especificaciones_huella_hash_registros.pdf  # noqa: B950
        expected_hash = (
            "3C464DAF61ACB827C65FDA19F352A4E3BDC2C640E9E9FC4CC058073F38F12F60"
        )
        issuerID = "89890001K"
        serialNumber = "12345678/G33"
        expeditionDate = "01-01-2024"
        documentType = "F1"
        amountTax = "12.35"
        amountTotal = "123.45"
        previousHash = ""
        registrationDate = "2024-01-01T19:20:30+01:00"
        verifactu_hash_string = (
            f"IDEmisorFactura={issuerID}&"
            f"NumSerieFactura={serialNumber}&"
            f"FechaExpedicionFactura={expeditionDate}&"
            f"TipoFactura={documentType}&"
            f"CuotaTotal={amountTax}&"
            f"ImporteTotal={amountTotal}&"
            f"Huella={previousHash}&"
            f"FechaHoraHusoGenRegistro={registrationDate}"
        )
        sha_hash_code = sha256(verifactu_hash_string.encode("utf-8"))
        hash_code = sha_hash_code.hexdigest().upper()
        self.assertEqual(hash_code, expected_hash)
