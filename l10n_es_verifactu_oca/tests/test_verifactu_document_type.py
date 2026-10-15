# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import re

from .common import TestVerifactuCommon


class TestVerifactuDocumentType(TestVerifactuCommon):
    """Regression tests for sealed VERI*FACTU document type (#5279)."""

    def test_tipofactura_matches_hash_after_partner_simplified_flag_change(self):
        """TipoFactura sealed in the hash must match the rebuilt AEAT payload.

        If the partner simplified-invoice flag changes after chaining, the payload
        must keep the TipoFactura used to compute Huella (OCA/l10n-spain#5279).
        """
        self._activate_certificate(self.certificate_password)
        self.partner.aeat_simplified_invoice = True
        invoice = self._create_and_prepare_invoice()
        invoice._generate_verifactu_chaining()

        hash_string = invoice.verifactu_hash_string or ""
        self.assertTrue(hash_string, "hash string must exist after chaining")
        match = re.search(r"TipoFactura=([A-Z0-9]+)", hash_string)
        self.assertTrue(match, f"TipoFactura missing in hash string: {hash_string}")
        tipo_in_hash = match.group(1)
        self.assertEqual(tipo_in_hash, "F2")
        self.assertEqual(invoice.verifactu_document_type, "F2")

        # Flip partner flag after seal (issue #5279 scenario)
        self.partner.aeat_simplified_invoice = False
        # Stored sealed value must not recompute from the partner flag
        invoice.invalidate_recordset(["verifactu_document_type"])
        self.assertEqual(
            invoice.verifactu_document_type,
            "F2",
            "sealed verifactu_document_type must stay F2 after partner flip",
        )
        self.assertFalse(
            self.partner.aeat_simplified_invoice,
            "partner flag flip must have taken effect",
        )

        payload = invoice._get_verifactu_invoice_dict()
        tipo_in_payload = payload["RegistroAlta"]["TipoFactura"]
        huella = payload["RegistroAlta"]["Huella"]

        self.assertEqual(
            huella,
            invoice.verifactu_hash,
            "payload Huella must reuse sealed hash",
        )
        self.assertEqual(
            tipo_in_payload,
            tipo_in_hash,
            "TipoFactura in payload diverged from TipoFactura sealed in hash "
            f"({tipo_in_hash!r} vs {tipo_in_payload!r})",
        )
        self.assertEqual(
            invoice.verifactu_document_type,
            "F2",
            "stored document type must remain sealed after payload rebuild",
        )
        self.assertNotIn(
            "Destinatarios",
            payload["RegistroAlta"],
            "F2 payload must not include Destinatarios",
        )
        self.assertEqual(
            payload["RegistroAlta"].get("FacturaSinIdentifDestinatarioArt61d"),
            "S",
        )
