# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError

from odoo.addons.l10n_es_aeat_sii_oca.tests.test_l10n_es_aeat_sii import (
    TestL10nEsAeatSiiBase,
)


class TestL10nEsAeatSiiMatch(TestL10nEsAeatSiiBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context,
                test_queue_job_no_delay=True,  # no jobs thanks
            )
        )
        cls.invoice.action_post()
        cls.invoice = cls.env[cls.invoice._name].browse(cls.invoice.id)

    def test_invoice_diffs_values(self):
        self._activate_certificate()
        invoice = self.invoice
        invoice.aeat_state = "sent"
        invoice.sii_csv = invoice._get_aeat_invoice_dict()
        res = invoice._get_diffs_values(invoice.sii_csv)
        self.assertEqual(res, [])

    def _aeat_consulta_response(self, csv):
        return {
            "RegistroRespuestaConsultaLRFacturasEmitidas": [
                {
                    "IDFactura": {"NumSerieFacturaEmisor": self.invoice.name},
                    "DatosPresentacion": {"CSV": csv},
                    "EstadoFactura": {
                        "EstadoRegistro": "AceptadoConCSV",
                        "EstadoCuadre": "5",
                    },
                }
            ]
        }

    def test_contrast_aeat_recovers_duplicate_error(self):
        """A "3000 - Factura duplicada" send error means AEAT already has the
        invoice registered, but Odoo never stored aeat_state/sii_csv. Contrasting
        it must recover the real send state, not just the informational fields.
        """
        self._activate_certificate()
        invoice = self.invoice
        invoice.write(
            {
                "aeat_state": "not_sent",
                "aeat_send_failed": True,
                "aeat_send_error": "3000 | Factura duplicada",
                "sii_csv": False,
            }
        )
        fake_serv = MagicMock()
        fake_serv.ConsultaLRFacturasEmitidas.return_value = (
            self._aeat_consulta_response("FAKECSV123")
        )
        with patch.object(type(invoice), "_connect_aeat", return_value=fake_serv):
            invoice.contrast_aeat()
        self.assertEqual(invoice.aeat_state, "sent")
        self.assertEqual(invoice.sii_csv, "FAKECSV123")
        self.assertFalse(invoice.aeat_send_error)
        self.assertFalse(invoice.aeat_send_failed)
        self.assertEqual(invoice.sii_contrast_state, "correct")

    def test_contrast_aeat_not_found_in_aeat(self):
        """When AEAT has no record at all, contrasting must not raise nor
        invent a send state - it just reports "no_exist" for manual review.
        """
        self._activate_certificate()
        invoice = self.invoice
        invoice.write(
            {
                "aeat_state": "not_sent",
                "aeat_send_failed": True,
                "aeat_send_error": "3000 | Factura duplicada",
                "sii_csv": False,
            }
        )
        fake_serv = MagicMock()
        fake_serv.ConsultaLRFacturasEmitidas.return_value = {
            "RegistroRespuestaConsultaLRFacturasEmitidas": []
        }
        with patch.object(type(invoice), "_connect_aeat", return_value=fake_serv):
            invoice.contrast_aeat()
        self.assertEqual(invoice.sii_contrast_state, "no_exist")
        self.assertFalse(invoice.sii_csv)
        self.assertEqual(invoice.aeat_state, "not_sent")

    def test_contrast_aeat_guard_rejects_never_sent(self):
        """An invoice that was never even attempted (no send, no failure) has
        nothing to contrast and must keep raising, as before."""
        invoice = self.invoice
        invoice.write(
            {"aeat_state": "not_sent", "aeat_send_failed": False, "sii_csv": False}
        )
        with self.assertRaises(UserError):
            invoice.contrast_aeat()
