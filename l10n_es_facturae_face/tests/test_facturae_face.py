# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import base64
import hashlib
import importlib.util
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import jwt
import requests
from cryptography import x509
from freezegun import freeze_time

from odoo import exceptions
from odoo.tools import mute_logger

from odoo.addons.edi_core_oca.tests.common import EDIBackendCommonTestCase
from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_certificate import (
    TestL10nEsAeatCertificateBase,
)
from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)


class TestL10nEsFacturaeFace(
    EDIBackendCommonTestCase, TestL10nEsAeatCertificateBase, TestL10nEsAeatModBase
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.http_error_response = requests.Response()
        cls.http_error_response.status_code = 400
        cls.http_error_response.url = "https://face.example.test/providers/v1/invoices"
        cls.env["ir.config_parameter"].sudo().set_param(
            "facturae.face.ws_rest",
            "https://face.example.test",
        )
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
        main_company = cls.company
        main_company.vat = "ESA12345674"
        main_company.partner_id.write(
            {
                "street": "Calle Mayor, 1",
                "city": "Madrid",
                "zip": "28001",
                "state_id": cls.env.ref("base.state_es_m").id,
                "country_id": cls.env.ref("base.es").id,
            }
        )
        eur = cls.env["res.currency"].search([("name", "in", ["EUR", "eur"])], limit=1)
        if not eur:
            eur = cls.env.ref("base.EUR")
        eur.write({"active": True, "name": "EUR"})
        main_company.currency_id = eur.id

        cls.env["res.currency.rate"].search([("currency_id", "=", eur.id)]).write(
            {"company_id": False}
        )
        if not cls.env["res.currency.rate"].search(
            [("currency_id", "=", eur.id)], limit=1
        ):
            cls.env["res.currency.rate"].create(
                {
                    "name": "2016-03-01",
                    "rate": 1.0,
                    "currency_id": eur.id,
                    "company_id": False,
                }
            )
        bank_obj = cls.env["res.partner.bank"]
        cls.bank = bank_obj.search(
            [("acc_number", "=", "FR20 1242 1242 1242 1242 1242 124")], limit=1
        )
        if not cls.bank:
            cls.bank = bank_obj.create(
                {
                    "acc_number": "FR20 1242 1242 1242 1242 1242 124",
                    "partner_id": main_company.partner_id.id,
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
        cls.product = cls.env["product.product"].create(
            {
                "name": "Producto de prueba",
                "type": "service",
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
                            "product_id": cls.product.id,
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
        cls.main_company = cls.company
        cls.main_company.face_email = "test@test.com"
        cls.face_update_type = cls.env.ref(
            "l10n_es_facturae_face.facturae_face_update_exchange_type"
        )

    def test_jwt_signature(self):
        self._activate_certificate(self.certificate_password)
        public_crt, private_key = self.env["l10n.es.aeat.certificate"].get_certificates(
            self.company
        )
        handler = self.env["l10n_es.facturae.face.base.handler"]
        token = handler.generate_jwt(public_crt, private_key)
        header = jwt.get_unverified_header(token)
        self.assertEqual(header["alg"], "RS256")
        self.assertEqual(header["typ"], "JWT")
        certificate = x509.load_der_x509_certificate(base64.b64decode(header["x5c"][0]))
        public_key = certificate.public_key()
        claims = jwt.decode(token, public_key, algorithms=["RS256"])
        self.assertEqual(
            claims["username"],
            hashlib.sha1(header["x5c"][0].encode("utf-8")).hexdigest(),
        )
        self.assertEqual(claims["exp"] - claims["iat"], 300)
        parts = token.split(".")
        parts[1] = (
            base64.urlsafe_b64encode(b'{"username":"tampered"}').rstrip(b"=").decode()
        )
        with self.assertRaises(jwt.InvalidSignatureError):
            jwt.decode(".".join(parts), public_key, algorithms=["RS256"])
        with freeze_time(datetime.now() + timedelta(minutes=6)):
            with self.assertRaises(jwt.ExpiredSignatureError):
                jwt.decode(token, public_key, algorithms=["RS256"])

    def test_http_requests(self):
        self._activate_certificate(self.certificate_password)
        public_crt, private_key = self.env["l10n.es.aeat.certificate"].get_certificates(
            self.company
        )
        handler = self.env["l10n_es.facturae.face.base.handler"]
        calls = [
            (
                "send_webservice",
                "post",
                "/providers/v1/invoices",
                (
                    "<Facturae/>",
                    "invoice.xml",
                    "test@example.com",
                    [SimpleNamespace(file_name="annex.txt", file_data="YW5uZXg=")],
                ),
            ),
            ("consult_invoice", "get", "/providers/v1/invoices/123", ("123",)),
            (
                "cancel",
                "post",
                "/providers/v1/invoices/123/cancellation-requests",
                ("123", "Cancellation reason"),
            ),
        ]
        for method, verb, path, args in calls:
            with self.subTest(method=method):
                response = mock.Mock()
                response.json.return_value = {"registryCode": "123"}
                with mock.patch(f"requests.{verb}", return_value=response) as request:
                    result = getattr(handler, method)(public_crt, private_key, *args)
                self.assertEqual(result, {"registryCode": "123"})
                request.assert_called_once()
                self.assertEqual(
                    request.call_args.args[0], "https://face.example.test" + path
                )
                self.assertEqual(request.call_args.kwargs["timeout"], 30)
                authorization = request.call_args.kwargs["headers"]["Authorization"]
                self.assertTrue(authorization.startswith("Bearer "))
                self.assertEqual(
                    jwt.get_unverified_header(authorization[7:])["alg"], "RS256"
                )
                response.raise_for_status.assert_called_once()
                if method == "send_webservice":
                    payload = request.call_args.kwargs["json"]
                    self.assertEqual(
                        base64.b64decode(payload["content"]), b"<Facturae/>"
                    )
                    self.assertEqual(payload["filename"], "invoice.xml")
                    self.assertEqual(payload["email"], "test@example.com")
                    self.assertEqual(
                        payload["attachments"],
                        [{"filename": "annex.txt", "content": "YW5uZXg="}],
                    )
                elif method == "cancel":
                    self.assertEqual(
                        request.call_args.kwargs["json"], {"comment": args[-1]}
                    )
                with (
                    mock.patch(
                        f"requests.{verb}", return_value=self.http_error_response
                    ),
                    self.assertRaisesRegex(exceptions.UserError, "400") as error,
                ):
                    getattr(handler, method)(public_crt, private_key, *args)
                self.assertIsInstance(error.exception.__cause__, requests.HTTPError)

    def test_migrate_rest_endpoint(self):
        path = (
            Path(__file__).resolve().parents[1]
            / "migrations/19.0.1.0.0/post-migration.py"
        )
        spec = importlib.util.spec_from_file_location("face_rest_migration", path)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        params = self.env["ir.config_parameter"].sudo()
        for old_url, new_url in [
            (
                "https://webservice.face.gob.es/facturasspp2?wsdl",
                "https://api.face.gob.es",
            ),
            (
                "https://se-face-webservice.redsara.es/facturasspp2?wsdl",
                "https://se-api-face.redsara.es",
            ),
        ]:
            with self.subTest(old_url=old_url):
                params.set_param("facturae.face.ws", old_url)
                migration.migrate.__wrapped__(self.env, "18.0.1.0.4")
                self.assertEqual(params.get_param("facturae.face.ws_rest"), new_url)
                self.assertFalse(params.get_param("facturae.face.ws"))
                migration.migrate.__wrapped__(self.env, "18.0.1.0.4")
                self.assertEqual(params.get_param("facturae.face.ws_rest"), new_url)

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

    @mute_logger("odoo.addons.queue_job.utils")
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
        with mock.patch("requests.post", return_value=self.http_error_response):
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

    @mute_logger("odoo.addons.queue_job.utils")
    def test_facturae_face_0(self):
        self._activate_certificate(self.certificate_password)
        with mock.patch("requests.post") as mock_client:
            mock_client.return_value = mock.Mock(
                status_code=200,
                json=lambda: {"registryCode": "REG1234567890"},
                raise_for_status=lambda: None,
            )
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
        with (
            mock.patch("requests.get", return_value=self.http_error_response),
            self.assertRaises(exceptions.UserError),
        ):
            self.move.with_context(
                _edi_receive_break_on_error=True
            ).edi_create_exchange_record(self.face_update_type.id)

    @mute_logger("odoo.addons.queue_job.utils")
    def test_facturae_face(self):
        self._activate_certificate(self.certificate_password)
        integration_code = "1234567890"
        with mock.patch("requests.post") as mock_client:
            mock_client.return_value = mock.Mock(
                status_code=200,
                json=lambda: {"registryCode": integration_code},
                raise_for_status=lambda: None,
            )
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
        self.move.invalidate_recordset()
        self.assertIn(
            self.face_update_type.id,
            [c["type"]["id"] for c in self.move.edi_config.values()],
        )
        with mock.patch("requests.get") as mock_client:
            mock_client.return_value = mock.Mock(
                status_code=200,
                json=lambda: {
                    "registryCode": integration_code,
                    "statusHistory": [{"code": "1200"}],
                    "cancellationRequestStatusCode": "4100",
                    "cancellationRequestComment": "MOTIVO",
                    "statusComment": "MOTIVO",
                },
                raise_for_status=lambda: None,
            )
            self.move.edi_create_exchange_record(self.face_update_type.id)
            mock_client.assert_called_once()
        self.assertEqual(exchange_record.l10n_es_facturae_status, "face-1200")
        self.assertEqual(self.move.l10n_es_facturae_status, "face-1200")
        with mock.patch("requests.get") as mock_client:
            mock_client.return_value = mock.Mock(
                status_code=200,
                json=lambda: {
                    "registryCode": integration_code,
                    "statusHistory": [{"code": "1200"}, {"code": "1300"}],
                    "cancellationRequestStatusCode": "4100",
                    "cancellationRequestComment": "MOTIVO",
                    "statusComment": "MOTIVO",
                },
                raise_for_status=lambda: None,
            )
            self.env["edi.exchange.record"].with_context()._cron_face_update_method()
        exchange_record.flush_recordset()
        exchange_record.invalidate_recordset()
        self.assertEqual(exchange_record.l10n_es_facturae_status, "face-1300")
        self.assertEqual(len(exchange_record.related_exchange_ids), 2)
        with mock.patch("requests.get") as mock_client:
            mock_client.return_value = mock.Mock(
                status_code=200,
                json=lambda: {
                    "registryCode": integration_code,
                    "statusHistory": [{"code": "1200"}, {"code": "1300"}],
                    "cancellationRequestStatusCode": "4100",
                    "cancellationRequestComment": "MOTIVO",
                    "statusComment": "MOTIVO",
                },
                raise_for_status=lambda: None,
            )
            self.env["edi.exchange.record"].with_context()._cron_face_update_method()
        exchange_record.flush_recordset()
        exchange_record.invalidate_recordset()
        self.assertEqual(len(exchange_record.related_exchange_ids), 2)
        # New record should not have been created
        cancel = self.env["edi.l10n.es.facturae.face.cancel"].create(
            {"move_id": self.move.id, "motive": "Anulacion"}
        )
        with (
            mock.patch("requests.post", return_value=self.http_error_response),
            self.assertRaises(exceptions.UserError),
        ):
            cancel.cancel_face()
        with mock.patch("requests.post") as mock_client:
            mock_client.return_value = mock.Mock(
                status_code=200,
                json=lambda: {
                    "registryCode": integration_code,
                },
                raise_for_status=lambda: None,
            )
            cancel.cancel_face()
        exchange_record.invalidate_recordset()
        self.assertEqual(
            exchange_record.l10n_es_facturae_cancellation_status, "face-4200"
        )
        self.assertEqual(self.move.l10n_es_facturae_cancellation_status, "face-4200")

    @mute_logger("odoo.addons.queue_job.utils")
    def test_facturae_face_cron_delayed(self):
        now = datetime.now()
        self._activate_certificate(self.certificate_password)
        integration_code = "1234567890"
        self.assertFalse(self.move.exchange_record_ids)
        with mock.patch("requests.post") as mock_client:
            mock_client.return_value = mock.Mock(
                status_code=200,
                json=lambda: {"registryCode": integration_code},
                raise_for_status=lambda: None,
            )
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

        with mock.patch("requests.get") as mock_client:
            mock_client.return_value = mock.Mock(
                status_code=200,
                json=lambda: {
                    "registryCode": integration_code,
                    "statusHistory": [{"code": "1200"}, {"code": "1300"}],
                    "cancellationRequestStatusCode": "4100",
                    "cancellationRequestComment": "MOTIVO",
                    "statusComment": "MOTIVO",
                },
                raise_for_status=lambda: None,
            )
            self.env["edi.exchange.record"].with_context()._cron_face_update_method(
                limit=1, days_limit=1
            )
            mock_client.assert_not_called()
            with freeze_time(now + timedelta(days=2)):
                self.env["edi.exchange.record"].with_context()._cron_face_update_method(
                    limit=1, days_limit=1
                )
            mock_client.assert_called_once()
        exchange_record.flush_recordset()
        exchange_record.invalidate_recordset()
        self.assertEqual(exchange_record.l10n_es_facturae_status, "face-1300")

        self.assertEqual(len(exchange_record.related_exchange_ids), 1)
        with mock.patch("requests.get") as mock_client:
            mock_client.return_value = mock.Mock(
                status_code=200,
                json=lambda: {
                    "registryCode": integration_code,
                    "statusHistory": [{"code": "1200"}, {"code": "1300"}],
                    "cancellationRequestStatusCode": "4100",
                    "cancellationRequestComment": "MOTIVO",
                    "statusComment": "MOTIVO",
                },
                raise_for_status=lambda: None,
            )
            with freeze_time(now + timedelta(days=4)):
                self.env["edi.exchange.record"].with_context()._cron_face_update_method(
                    limit=1, days_limit=1
                )
            mock_client.assert_called_once()
        exchange_record.flush_recordset()
        exchange_record.invalidate_recordset()
        self.assertEqual(len(exchange_record.related_exchange_ids), 1)
