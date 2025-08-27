# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from unittest import mock

import requests

from odoo import exceptions

from odoo.addons.edi_core_oca.tests.common import EDIBackendCommonTestCase
from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_certificate import (
    TestL10nEsAeatCertificateBase,
)

_logger = logging.getLogger(__name__)
try:
    from zeep import Client
except (OSError, ImportError) as err:
    _logger.info(err)


class TestL10nEsFacturaeFace(EDIBackendCommonTestCase, TestL10nEsAeatCertificateBase):
    @classmethod
    def setUpClass(cls):
        cls._super_send = requests.Session.send
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.tax = cls.env["account.tax"].create(
            {
                "name": "Test tax",
                "amount_type": "percent",
                "amount": 21,
                "type_tax_use": "sale",
                "facturae_code": "01",
            }
        )

        cls.state = cls.env["res.country.state"].create(
            {
                "name": "Ciudad Real",
                "code": "13",
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Cliente de prueba",
                "street": "C/ Ejemplo, 13",
                "zip": "13700",
                "city": "Tomelloso",
                "state_id": cls.state.id,
                "country_id": cls.env.ref("base.es").id,
                "vat": "ES05680675C",
                "facturae": True,
                "attach_invoice_as_annex": False,
                "organo_gestor": "U00000038",
                "unidad_tramitadora": "U00000038",
                "oficina_contable": "U00000038",
                "l10n_es_facturae_sending_code": "face",
            }
        )
        main_company = cls.env.ref("base.main_company")
        main_company.vat = "ESA12345674"
        main_company.partner_id.country_id = cls.env.ref("base.uk")
        cls.env["res.currency.rate"].search(
            [("currency_id", "=", main_company.currency_id.id)]
        ).write({"company_id": False})
        bank_obj = cls.env["res.partner.bank"]
        cls.bank = bank_obj.search(
            [("acc_number", "=", "FR20 1242 1242 1242 1242 1242 124")], limit=1
        )
        if not cls.bank:
            cls.bank = bank_obj.create(
                {
                    "acc_number": "FR20 1242 1242 1242 1242 1242 124",
                    "partner_id": main_company.partner.id,
                    "bank_id": cls.env["res.bank"]
                    .search([("bic", "=", "PSSTFRPPXXX")], limit=1)
                    .id,
                }
            )
        cls.payment_method = cls.env.ref("account.account_payment_method_manual_in")
        payment_methods = cls.env["account.payment.method"].search(
            [("payment_type", "=", "inbound")]
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Test journal",
                "code": "TEST",
                "type": "bank",
                "company_id": main_company.id,
                "bank_account_id": cls.bank.id,
                "inbound_payment_method_line_ids": [
                    (0, 0, {"payment_method_id": x.id}) for x in payment_methods
                ],
            }
        )

        cls.sale_journal = cls.env["account.journal"].create(
            {
                "name": "Sale journal",
                "code": "SALE_TEST",
                "type": "sale",
                "company_id": main_company.id,
            }
        )
        cls.payment_mode = cls.env["account.payment.mode"].create(
            {
                "name": "Test payment mode",
                "bank_account_link": "fixed",
                "fixed_journal_id": cls.journal.id,
                "payment_method_id": cls.payment_method.id,
                "show_bank_account_from_journal": True,
                "facturae_code": "01",
            }
        )

        cls.payment_mode_02 = cls.env["account.payment.mode"].create(
            {
                "name": "Test payment mode 02",
                "bank_account_link": "fixed",
                "fixed_journal_id": cls.journal.id,
                "payment_method_id": cls.payment_method.id,
                "show_bank_account_from_journal": True,
                "facturae_code": "02",
            }
        )

        cls.account = cls.env["account.account"].create(
            {
                "company_ids": [(4, main_company.id)],
                "name": "Facturae Product account",
                "code": "facturaeproduct",
                "account_type": "income",
            }
        )
        cls.move = cls.env["account.move"].create(
            {
                "partner_id": cls.partner.id,
                "journal_id": cls.sale_journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": cls.payment_mode.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": cls.env.ref("product.product_delivery_02").id,
                            "account_id": cls.account.id,
                            "name": "Producto de prueba",
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "tax_ids": [(6, 0, cls.tax.ids)],
                        },
                    )
                ],
            }
        )
        cls.main_company = cls.env.ref("base.main_company")
        cls.main_company.face_email = "test@test.com"
        cls.face_update_type = cls.env.ref(
            "l10n_es_facturae_face.facturae_face_update_exchange_type"
        )

    # Don't block external requests.
    @classmethod
    def _request_handler(cls, s, r, /, **kw):
        return cls._super_send(s, r, **kw)

    def test_constrain_company_mail(self):
        with self.assertRaises(exceptions.ValidationError):
            self.main_company.face_email = "test"

    def test_constrain_partner_facturae(self):
        with self.assertRaises(exceptions.ValidationError):
            self.partner.facturae = False

    def test_constrain_partner_vat(self):
        with self.assertRaises(exceptions.ValidationError):
            self.partner.vat = False

    def test_constrain_partner_country(self):
        with self.assertRaises(exceptions.ValidationError):
            self.partner.country_id = False

    def test_constrain_partner_spain_no_state(self):
        with self.assertRaises(exceptions.ValidationError):
            self.partner.state_id = False

    def test_facturae_face_error(self):
        self._activate_certificate(self.certificate_password)
        self.assertFalse(self.move.exchange_record_ids)
        self.move.with_context(
            force_edi_send=True, test_queue_job_no_delay=True
        ).action_post()
        self.move.invalidate_recordset()
        self.assertTrue(self.move.exchange_record_ids)
        exchange_record = self.move.exchange_record_ids
        self.assertEqual(exchange_record.edi_exchange_state, "output_pending")
        exchange_record.backend_id.exchange_send(exchange_record)
        self.assertEqual(exchange_record.edi_exchange_state, "output_error_on_send")

    def test_create_facturae_file_without_organo_gestor(self):
        self._activate_certificate(self.certificate_password)
        self.move.action_post()
        self.move.name = "2999/99999"
        wizard = (
            self.env["create.facturae"]
            .with_context(active_ids=self.move.ids, active_model="account.move")
            .create({})
        )
        self.partner.organo_gestor = False
        with self.assertRaises(exceptions.ValidationError):
            wizard.create_facturae_file()

    def test_create_facturae_file_without_unidad_tramitadora(self):
        self._activate_certificate(self.certificate_password)
        self.move.action_post()
        self.move.name = "2999/99999"
        wizard = (
            self.env["create.facturae"]
            .with_context(active_ids=self.move.ids, active_model="account.move")
            .create({})
        )
        self.partner.unidad_tramitadora = False
        with self.assertRaises(exceptions.ValidationError):
            wizard.create_facturae_file()

    def test_create_facturae_file_without_oficina_contable(self):
        self._activate_certificate(self.certificate_password)
        self.move.action_post()
        self.move.name = "2999/99999"
        wizard = (
            self.env["create.facturae"]
            .with_context(active_ids=self.move.ids, active_model="account.move")
            .create({})
        )
        self.partner.oficina_contable = False
        with self.assertRaises(exceptions.ValidationError):
            wizard.create_facturae_file()

    def test_facturae_face_0(self):
        class DemoService:
            def __init__(self, value):
                self.value = value

            def enviarFactura(self, *args):
                return self.value

            def anularFactura(self, *args):
                return self.value

            def consultarFactura(self, *args):
                return self.value

            def consultarListadoFacturas(self, *args):
                return self.value

        self._activate_certificate(self.certificate_password)
        client = Client(
            wsdl=self.env["ir.config_parameter"].sudo().get_param("facturae.face.ws")
        )
        integration_code = "1234567890"
        response_ok = client.get_type("ns0:EnviarFacturaResponse")(
            client.get_type("ns0:Resultado")(codigo="0", descripcion="OK"),
            client.get_type("ns0:EnviarFactura")(numeroRegistro=integration_code),
        )
        self.assertFalse(self.move.exchange_record_ids)
        with mock.patch("zeep.client.ServiceProxy") as mock_client:
            mock_client.return_value = DemoService(response_ok)

            self.move.with_context(
                force_edi_send=True, test_queue_job_no_delay=True
            ).action_post()
            self.move.name = "2999/99998"
            mock_client.assert_not_called()
            exchange_record = self.move.exchange_record_ids.with_context(
                _edi_send_break_on_error=True
            )
            self.assertEqual(exchange_record.edi_exchange_state, "output_pending")
            exchange_record.backend_id.exchange_send(exchange_record)
            self.assertEqual(
                exchange_record.edi_exchange_state, "output_sent_and_processed"
            )
            mock_client.assert_called_once()
        self.move.invalidate_recordset()
        self.assertTrue(self.move.exchange_record_ids)
        self.assertIn(
            self.face_update_type.id,
            [c["type"]["id"] for c in self.move.edi_config.values()],
        )
        result = self.move.with_context().edi_create_exchange_record(
            self.face_update_type.id
        )
        record = self.env[result["res_model"]].browse(result["res_id"])
        self.assertEqual("input_receive_error", record.edi_exchange_state)

    def test_facturae_face(self):
        class DemoService:
            def __init__(self, value):
                self.value = value

            def enviarFactura(self, *args):
                return self.value

            def anularFactura(self, *args):
                return self.value

            def consultarFactura(self, *args):
                return self.value

            def consultarListadoFacturas(self, *args):
                return self.value

        self._activate_certificate(self.certificate_password)
        client = Client(
            wsdl=self.env["ir.config_parameter"].sudo().get_param("facturae.face.ws")
        )
        integration_code = "1234567890"
        response_ok = client.get_type("ns0:EnviarFacturaResponse")(
            client.get_type("ns0:Resultado")(codigo="0", descripcion="OK"),
            client.get_type("ns0:EnviarFactura")(numeroRegistro=integration_code),
        )
        self.assertFalse(self.move.exchange_record_ids)
        with mock.patch("zeep.client.ServiceProxy") as mock_client:
            mock_client.return_value = DemoService(response_ok)

            self.move.with_context(
                force_edi_send=True, test_queue_job_no_delay=True
            ).action_post()
            self.move.name = "2999/99998"
            mock_client.assert_not_called()
            exchange_record = self.move.exchange_record_ids.with_context(
                _edi_send_break_on_error=True
            )
            self.assertEqual(exchange_record.edi_exchange_state, "output_pending")
            exchange_record.backend_id.exchange_send(exchange_record)
            self.assertEqual(
                exchange_record.edi_exchange_state, "output_sent_and_processed"
            )
            mock_client.assert_called_once()
        self.move.invalidate_recordset()
        self.assertTrue(self.move.exchange_record_ids)
        exchange_record = self.move.exchange_record_ids
        response_update = client.get_type("ns0:ConsultarFacturaResponse")(
            client.get_type("ns0:Resultado")(codigo="0", descripcion="OK"),
            client.get_type("ns0:ConsultarFactura")(
                "1234567890",
                client.get_type("ns0:EstadoFactura")("1200", "DESC", "MOTIVO"),
                client.get_type("ns0:EstadoFactura")("4100", "DESC", "MOTIVO"),
            ),
        )
        self.move.invalidate_recordset()
        self.assertIn(
            self.face_update_type.id,
            [c["type"]["id"] for c in self.move.edi_config.values()],
        )
        try:
            self.move.edi_create_exchange_record(self.face_update_type.id)
        except exceptions.UserError:  # pylint: disable=W8138
            pass
        except Exception:
            raise

        with mock.patch("zeep.client.ServiceProxy") as mock_client:
            mock_client.return_value = DemoService(response_update)
            self.move.edi_create_exchange_record(self.face_update_type.id)
            mock_client.assert_called_once()
        self.assertEqual(exchange_record.l10n_es_facturae_status, "face-1200")
        self.assertEqual(self.move.l10n_es_facturae_status, "face-1200")
        # On the second update, no new logs are generated
        multi_response = client.get_type("ns0:ConsultarListadoFacturaResponse")(
            client.get_type("ns0:Resultado")(codigo="0", descripcion="OK"),
            client.get_type("ns0:ArrayOfConsultarListadoFactura")(
                [
                    client.get_type("ns0:ConsultarListadoFactura")(
                        codigo="0",
                        descripcion="OK",
                        factura=client.get_type("ns0:ConsultarFactura")(
                            "1234567890",
                            client.get_type("ns0:EstadoFactura")(
                                "1300", "DESC", "MOTIVO"
                            ),
                            client.get_type("ns0:EstadoFactura")(
                                "4100", "DESC", "MOTIVO"
                            ),
                        ),
                    )
                ]
            ),
        )

        with mock.patch("zeep.client.ServiceProxy") as mock_client:
            mock_client.return_value = DemoService(multi_response)
            self.env["edi.exchange.record"].with_context()._cron_face_update_method()
        exchange_record.flush_recordset()
        exchange_record.invalidate_recordset()
        self.assertEqual(exchange_record.l10n_es_facturae_status, "face-1300")

        self.assertEqual(len(exchange_record.related_exchange_ids), 3)
        with mock.patch("zeep.client.ServiceProxy") as mock_client:
            mock_client.return_value = DemoService(multi_response)
            self.env["edi.exchange.record"].with_context()._cron_face_update_method()
        exchange_record.flush_recordset()
        exchange_record.invalidate_recordset()
        self.assertEqual(len(exchange_record.related_exchange_ids), 3)
        # New record should not have been created
        cancel = self.env["edi.l10n.es.facturae.face.cancel"].create(
            {"move_id": self.move.id, "motive": "Anulacion"}
        )
        with self.assertRaises(exceptions.UserError):
            cancel.cancel_face()
        response_cancel = client.get_type("ns0:ConsultarFacturaResponse")(
            client.get_type("ns0:Resultado")("0", "OK"),
            client.get_type("ns0:AnularFactura")("1234567890", "ANULADO"),
        )
        with mock.patch("zeep.client.ServiceProxy") as mock_client:
            mock_client.return_value = DemoService(response_cancel)
            cancel.cancel_face()
        exchange_record.invalidate_recordset()
        self.assertEqual(
            exchange_record.l10n_es_facturae_cancellation_status, "face-4200"
        )
        self.assertEqual(self.move.l10n_es_facturae_cancellation_status, "face-4200")
