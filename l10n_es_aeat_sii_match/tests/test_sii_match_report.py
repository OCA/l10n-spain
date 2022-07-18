# © 2022 FactorLibre - Javier Iniesta <javier.iniesta@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import base64
from unittest.mock import MagicMock, patch
from odoo import fields
from odoo.exceptions import AccessError
from odoo.addons.l10n_es_aeat_sii.tests.test_l10n_es_aeat_sii import (
    CERTIFICATE_PATH,
    CERTIFICATE_PASSWD,
    TestL10nEsAeatSiiBase,
)
from odoo.addons.l10n_es_aeat_sii.models.account_invoice import AccountInvoice
from odoo.tests.common import at_install, post_install
from ..models.aeat_sii_match_report import SiiMatchReport


@post_install(True)
@at_install(False)
class TestL10nEsAeatSiiMatch(TestL10nEsAeatSiiBase):
    @classmethod
    def _activate_certificate(cls):
        """Obtain Keys from .pfx and activate the cetificate"""
        wizard = cls.env["l10n.es.aeat.sii.password"].create(
            {
                "password": CERTIFICATE_PASSWD,
                "folder": "test",
            }
        )
        wizard.with_context(active_id=cls.sii_cert.id).get_keys()
        cls.sii_cert.action_activate()
        cls.sii_cert.company_id.write(
            {
                "name": "ENTIDAD FICTICIO ACTIVO",
                "vat": "ESJ7102572J",
            }
        )

    @classmethod
    def setUpClass(cls):
        def _call_side_effect_send_invoice(*args, **kwargs):
            return

        cls.mock_call = MagicMock(side_effect=_call_side_effect_send_invoice)

        super().setUpClass()
        cls.company.use_connector = False
        with open(CERTIFICATE_PATH, "rb") as certificate:
            content = certificate.read()
        cls.sii_cert = cls.env["l10n.es.aeat.sii"].create(
            {
                "name": "Test Certificate",
                "file": base64.b64encode(content),
                "company_id": cls.invoice.company_id.id,
            }
        )
        cls._activate_certificate()
        cls.user = cls.env["res.users"].create(
            {
                "name": "Test user",
                "login": "test_user",
                "groups_id": [(4, cls.env.ref("l10n_es_aeat.group_account_aeat").id)],
                "email": "somebody@somewhere.com",
            }
        )
        cls.user_not_allowed = cls.env["res.users"].create(
            {
                "name": "Test user 2",
                "login": "test_user_2",
                "groups_id": [(4, cls.env.ref("account.group_account_invoice").id)],
                "email": "somebody2@somewhere.com",
            }
        )
        with patch.object(AccountInvoice, "_send_invoice_to_sii", new=cls.mock_call):
            cls.invoice.with_context(test_queue_job_no_delay=True).action_invoice_open()
        cls.invoice.number = "INV001"
        cls.invoice.sii_csv = "XXXXXXXXXXXXXXXX"
        invoice_date = (
            cls.invoice.date[-2:] + cls.invoice.date[4:8] + cls.invoice.date[:4]
        )
        detail = [
            {
                "TipoImpositivo": str(cls.invoice.tax_line_ids.tax_id.amount),
                "BaseImponible": str(cls.invoice.tax_line_ids.base),
                "CuotaRepercutida": str(cls.invoice.tax_line_ids.amount),
                "TipoRecargoEquivalencia": None,
                "CuotaRecargoEquivalencia": None,
            }
        ]
        fact_key = "FacturacionDispAdicionalTerceraYsextayDelMercadoOrganizadoDelGas"
        cls.res_line = [
            {
                "IDFactura": {
                    "IDEmisorFactura": {"NIF": cls.company.vat},
                    "NumSerieFacturaEmisor": cls.invoice.number,
                    "NumSerieFacturaEmisorResumenFin": None,
                    "FechaExpedicionFacturaEmisor": invoice_date,
                },
                "DatosFacturaEmitida": {
                    "TipoFactura": "F1",
                    "TipoRectificativa": None,
                    "FacturasAgrupadas": None,
                    "FacturasRectificadas": None,
                    "ImporteRectificacion": None,
                    "FechaOperacion": None,
                    "ClaveRegimenEspecialOTrascendencia": "01",
                    "ClaveRegimenEspecialOTrascendenciaAdicional1": None,
                    "ClaveRegimenEspecialOTrascendenciaAdicional2": None,
                    "NumRegistroAcuerdoFacturacion": None,
                    "ImporteTotal": "23.64",
                    "BaseImponibleACoste": None,
                    "DescripcionOperacion": "Factura de venta | "
                    + cls.invoice.invoice_line_ids.name,
                    "RefExterna": None,
                    "FacturaSimplificadaArticulos7.2_7.3": None,
                    "EntidadSucedida": None,
                    "RegPrevioGGEEoREDEMEoCompetencia": None,
                    "Macrodato": None,
                    "DatosInmueble": None,
                    "ImporteTransmisionInmueblesSujetoAIVA": None,
                    "EmitidaPorTercerosODestinatario": "N",
                    fact_key: None,
                    "VariosDestinatarios": "N",
                    "Cupon": None,
                    "FacturaSinIdentifDestinatarioAritculo6.1.d": None,
                    "Contraparte": {
                        "NombreRazon": cls.invoice.partner_id.name,
                        "NIFRepresentante": None,
                        "NIF": cls.invoice.partner_id.vat,
                        "IDOtro": None,
                    },
                    "TipoDesglose": {
                        "DesgloseFactura": {
                            "Sujeta": {
                                "Exenta": None,
                                "NoExenta": {
                                    "TipoNoExenta": "S1",
                                    "DesgloseIVA": {"DetalleIVA": detail},
                                },
                            },
                            "NoSujeta": None,
                        },
                        "DesgloseTipoOperacion": None,
                    },
                    "Cobros": "N",
                },
                "DatosPresentacion": {
                    "NIFPresentador": cls.company.vat,
                    "TimestampPresentacion": invoice_date + " 10:42:26",
                    "CSV": cls.invoice.sii_csv,
                },
                "EstadoFactura": {
                    "EstadoCuadre": "4",
                    "TimestampEstadoCuadre": invoice_date + " 10:43:30",
                    "TimestampUltimaModificacion": invoice_date + " 10:43:29",
                    "EstadoRegistro": "Correcta",
                    "CodigoErrorRegistro": None,
                    "DescripcionErrorRegistro": None,
                },
                "DatosDescuadreContraparte": None,
            }
        ]
        cls.report = cls.env["l10n.es.aeat.sii.match.report"].create(
            {
                "name": "TEST REPORT 001",
                "period_type": "01",
                "fiscalyear": 2018,
                "invoice_type": "out",
            }
        )

        def _call_side_effect_get_invoice(*args, **kwargs):
            match_vals = {}
            (
                match_vals["sii_match_result"],
                summary,
            ) = cls.report._get_match_result_values(cls.res_line)
            match_vals.update(
                {
                    "number_records": summary.get("total", 0),
                    "number_records_both": summary.get("both", 0),
                    "number_records_odoo": summary.get("odoo", 0),
                    "number_records_sii": summary.get("sii", 0),
                    "number_records_correct": summary.get("correct", 0),
                    "number_records_no_exist": summary.get("no_exist", 0),
                    "number_records_partially": summary.get("partially", 0),
                    "number_records_no_test": summary.get("no_test", 0),
                    "number_records_in_process": summary.get("in_process", 0),
                    "number_records_not_contrasted": summary.get("not_contrasted", 0),
                    "number_records_partially_contrasted": summary.get(
                        "partially_contrasted", 0
                    ),
                    "number_records_contrasted": summary.get("contrasted", 0),
                }
            )
            cls.report.sii_match_result.mapped("sii_match_difference_ids").unlink()
            cls.report.sii_match_result.unlink()
            match_vals["state"] = "calculated"
            match_vals["calculate_date"] = fields.Datetime.now()
            cls.report.write(match_vals)

        cls.mock_call = MagicMock(side_effect=_call_side_effect_get_invoice)

    def test_sii_match_report_state_1(self):
        self.res_line[0]["EstadoFactura"]["EstadoCuadre"] = "1"
        with patch.object(
            SiiMatchReport, "_process_invoices_from_sii", new=self.mock_call
        ):
            self.report.with_context(test_queue_job_no_delay=True).sudo(
                self.user
            ).button_calculate()
        res = self.report.open_result()
        result = self.env[res["res_model"]].search(res["domain"])
        self.assertEqual(self.report.number_records, 1)
        self.assertEqual(self.report.number_records_both, 1)
        self.assertEqual(self.report.number_records_odoo, 0)
        self.assertEqual(self.report.number_records_sii, 0)
        self.assertEqual(self.report.number_records_correct, 1)
        self.assertEqual(self.report.number_records_no_exist, 0)
        self.assertEqual(self.report.number_records_partially, 0)
        self.assertEqual(self.report.number_records_no_test, 1)
        self.assertEqual(self.report.number_records_in_process, 0)
        self.assertEqual(self.report.number_records_not_contrasted, 0)
        self.assertEqual(self.report.number_records_partially_contrasted, 0)
        self.assertEqual(self.report.number_records_contrasted, 0)
        self.assertFalse(result)

    def test_sii_match_report_state_2(self):
        self.res_line[0]["EstadoFactura"]["EstadoCuadre"] = "2"
        with patch.object(
            SiiMatchReport, "_process_invoices_from_sii", new=self.mock_call
        ):
            self.report.with_context(test_queue_job_no_delay=True).sudo(
                self.user
            ).button_calculate()
        res = self.report.open_result()
        result = self.env[res["res_model"]].search(res["domain"])
        self.assertEqual(self.report.number_records, 1)
        self.assertEqual(self.report.number_records_both, 1)
        self.assertEqual(self.report.number_records_odoo, 0)
        self.assertEqual(self.report.number_records_sii, 0)
        self.assertEqual(self.report.number_records_correct, 1)
        self.assertEqual(self.report.number_records_no_exist, 0)
        self.assertEqual(self.report.number_records_partially, 0)
        self.assertEqual(self.report.number_records_no_test, 0)
        self.assertEqual(self.report.number_records_in_process, 1)
        self.assertEqual(self.report.number_records_not_contrasted, 0)
        self.assertEqual(self.report.number_records_partially_contrasted, 0)
        self.assertEqual(self.report.number_records_contrasted, 0)
        self.assertFalse(result)

    def test_sii_match_report_state_3(self):
        self.res_line[0]["EstadoFactura"]["EstadoCuadre"] = "3"
        with patch.object(
            SiiMatchReport, "_process_invoices_from_sii", new=self.mock_call
        ):
            self.report.with_context(test_queue_job_no_delay=True).sudo(
                self.user
            ).button_calculate()
        res = self.report.open_result()
        result = self.env[res["res_model"]].search(res["domain"])
        self.assertEqual(self.report.number_records, 1)
        self.assertEqual(self.report.number_records_both, 1)
        self.assertEqual(self.report.number_records_odoo, 0)
        self.assertEqual(self.report.number_records_sii, 0)
        self.assertEqual(self.report.number_records_correct, 1)
        self.assertEqual(self.report.number_records_no_exist, 0)
        self.assertEqual(self.report.number_records_partially, 0)
        self.assertEqual(self.report.number_records_no_test, 0)
        self.assertEqual(self.report.number_records_in_process, 0)
        self.assertEqual(self.report.number_records_not_contrasted, 1)
        self.assertEqual(self.report.number_records_partially_contrasted, 0)
        self.assertEqual(self.report.number_records_contrasted, 0)
        self.assertFalse(result)

    def test_sii_match_report_state_4(self):
        self.res_line[0]["EstadoFactura"]["EstadoCuadre"] = "4"
        with patch.object(
            SiiMatchReport, "_process_invoices_from_sii", new=self.mock_call
        ):
            self.report.with_context(test_queue_job_no_delay=True).sudo(
                self.user
            ).button_calculate()

        res = self.report.open_result()
        result = self.env[res["res_model"]].search(res["domain"])
        self.assertEqual(self.report.number_records, 1)
        self.assertEqual(self.report.number_records_both, 1)
        self.assertEqual(self.report.number_records_odoo, 0)
        self.assertEqual(self.report.number_records_sii, 0)
        self.assertEqual(self.report.number_records_correct, 1)
        self.assertEqual(self.report.number_records_no_exist, 0)
        self.assertEqual(self.report.number_records_partially, 0)
        self.assertEqual(self.report.number_records_no_test, 0)
        self.assertEqual(self.report.number_records_in_process, 0)
        self.assertEqual(self.report.number_records_not_contrasted, 0)
        self.assertEqual(self.report.number_records_partially_contrasted, 1)
        self.assertEqual(self.report.number_records_contrasted, 0)
        self.assertEqual(result.sii_match_state, "4")
        self.assertEqual(result.sii_contrast_state, "correct")

    def test_sii_match_report_state_5(self):
        self.res_line[0]["EstadoFactura"]["EstadoCuadre"] = "5"
        with patch.object(
            SiiMatchReport, "_process_invoices_from_sii", new=self.mock_call
        ):
            self.report.with_context(test_queue_job_no_delay=True).sudo(
                self.user
            ).button_calculate()
        res = self.report.open_result()
        result = self.env[res["res_model"]].search(res["domain"])
        self.assertEqual(self.report.number_records, 1)
        self.assertEqual(self.report.number_records_both, 1)
        self.assertEqual(self.report.number_records_odoo, 0)
        self.assertEqual(self.report.number_records_sii, 0)
        self.assertEqual(self.report.number_records_correct, 1)
        self.assertEqual(self.report.number_records_no_exist, 0)
        self.assertEqual(self.report.number_records_partially, 0)
        self.assertEqual(self.report.number_records_no_test, 0)
        self.assertEqual(self.report.number_records_in_process, 0)
        self.assertEqual(self.report.number_records_not_contrasted, 0)
        self.assertEqual(self.report.number_records_partially_contrasted, 0)
        self.assertEqual(self.report.number_records_contrasted, 1)
        self.assertFalse(result)

    def test_sii_match_report_state_transition(self):
        report = (
            self.env["l10n.es.aeat.sii.match.report"]
            .sudo(self.user)
            .create(
                {
                    "name": "TEST REPORT 005",
                    "period_type": "01",
                    "fiscalyear": 2018,
                    "invoice_type": "out",
                }
            )
        )
        report.button_cancel()
        self.assertEqual(report.state, "cancelled")
        report.button_recover()
        self.assertEqual(report.state, "draft")
        report.button_confirm()
        self.assertEqual(report.state, "done")

    def test_sii_match_report_user_not_allowed(self):
        with self.assertRaises(AccessError):
            self.env["l10n.es.aeat.sii.match.report"].sudo(
                self.user_not_allowed
            ).create(
                {
                    "name": "TEST REPORT 010",
                    "period_type": "01",
                    "fiscalyear": 2018,
                    "invoice_type": "out",
                }
            )
