# Copyright 2017 Creu Blanca
# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


import base64
import logging
import os

from odoo import exceptions, tools
from odoo.tests import common

from odoo.addons.component.tests.common import SavepointComponentRegistryCase

_logger = logging.getLogger(__name__)
try:
    from OpenSSL import crypto
except (ImportError, IOError) as err:
    _logger.info(err)


@common.tagged("-at_install", "post_install")
class EDIBackendTestCase(SavepointComponentRegistryCase, common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(
            context=dict(
                cls.env.context, tracking_disable=True, test_queue_job_no_delay=True
            )
        )

        self = cls

        self._load_module_components(self, "component_event")
        self._load_module_components(self, "edi")
        self._load_module_components(self, "storage_backend")
        self._load_module_components(self, "edi_storage")
        self._load_module_components(self, "edi_account")
        self._load_module_components(self, "l10n_es_facturae")
        self._load_module_components(self, "l10n_es_facturae_efact")
        pkcs12 = crypto.PKCS12()
        pkey = crypto.PKey()
        pkey.generate_key(crypto.TYPE_RSA, 512)
        x509 = crypto.X509()
        x509.set_pubkey(pkey)
        x509.set_serial_number(0)
        x509.get_subject().CN = "me"
        x509.set_issuer(x509.get_subject())
        x509.gmtime_adj_notBefore(0)
        x509.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
        x509.sign(pkey, "md5")
        pkcs12.set_privatekey(pkey)
        pkcs12.set_certificate(x509)
        self.tax = self.env["account.tax"].create(
            {
                "name": "Test tax",
                "amount_type": "percent",
                "amount": 21,
                "type_tax_use": "sale",
                "facturae_code": "01",
            }
        )

        self.state = self.env["res.country.state"].create(
            {
                "name": "Ciudad Real",
                "code": "13",
                "country_id": self.env.ref("base.es").id,
            }
        )
        self.partner = self.env["res.partner"].create(
            {
                "name": "Cliente de prueba",
                "street": "C/ Ejemplo, 13",
                "zip": "13700",
                "city": "Tomelloso",
                "state_id": self.state.id,
                "country_id": self.env.ref("base.es").id,
                "vat": "ES05680675C",
                "facturae": True,
                "attach_invoice_as_annex": False,
                "organo_gestor": "U00000038",
                "unidad_tramitadora": "U00000038",
                "oficina_contable": "U00000038",
                "l10n_es_facturae_sending_code": "efact",
                "facturae_efact_code": "0123456789012345678901",
            }
        )
        main_company = self.env.ref("base.main_company")
        main_company.vat = "ESA12345674"
        main_company.partner_id.country_id = self.env.ref("base.uk")
        main_company.facturae_cert = base64.b64encode(
            pkcs12.export(passphrase="password")
        )
        main_company.facturae_cert_password = "password"
        main_company.partner_id.facturae_efact_code = "0123456789012345678901"
        self.env["res.currency.rate"].search(
            [("currency_id", "=", main_company.currency_id.id)]
        ).write({"company_id": False})
        bank_obj = self.env["res.partner.bank"]
        self.bank = bank_obj.search(
            [("acc_number", "=", "FR20 1242 1242 1242 1242 1242 124")], limit=1
        )
        if not self.bank:
            self.bank = bank_obj.create(
                {
                    "acc_number": "FR20 1242 1242 1242 1242 1242 124",
                    "partner_id": main_company.partner.id,
                    "bank_id": self.env["res.bank"]
                    .search([("bic", "=", "PSSTFRPPXXX")], limit=1)
                    .id,
                }
            )
        self.payment_method = self.env["account.payment.method"].create(
            {
                "name": "inbound_mandate",
                "code": "inbound_mandate",
                "payment_type": "inbound",
                "bank_account_required": False,
                "active": True,
            }
        )
        payment_methods = self.env["account.payment.method"].search(
            [("payment_type", "=", "inbound")]
        )
        self.journal = self.env["account.journal"].create(
            {
                "name": "Test journal",
                "code": "TEST",
                "type": "bank",
                "company_id": main_company.id,
                "bank_account_id": self.bank.id,
                "inbound_payment_method_ids": [(6, 0, payment_methods.ids)],
            }
        )

        self.sale_journal = self.env["account.journal"].create(
            {
                "name": "Sale journal",
                "code": "SALE_TEST",
                "type": "sale",
                "company_id": main_company.id,
            }
        )
        self.payment_mode = self.env["account.payment.mode"].create(
            {
                "name": "Test payment mode",
                "bank_account_link": "fixed",
                "fixed_journal_id": self.journal.id,
                "payment_method_id": self.env.ref(
                    "payment.account_payment_method_electronic_in"
                ).id,
                "show_bank_account_from_journal": True,
                "facturae_code": "01",
            }
        )

        self.payment_mode_02 = self.env["account.payment.mode"].create(
            {
                "name": "Test payment mode 02",
                "bank_account_link": "fixed",
                "fixed_journal_id": self.journal.id,
                "payment_method_id": self.payment_method.id,
                "show_bank_account_from_journal": True,
                "facturae_code": "02",
            }
        )

        self.account = self.env["account.account"].create(
            {
                "company_id": main_company.id,
                "name": "Facturae Product account",
                "code": "facturae_product",
                "user_type_id": self.env.ref("account.data_account_type_revenue").id,
            }
        )
        self.move = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                # "account_id": self.partner.property_account_receivable_id.id,
                "journal_id": self.sale_journal.id,
                "invoice_date": "2016-03-12",
                "payment_mode_id": self.payment_mode.id,
                "type": "out_invoice",
                "name": "R/0001",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.env.ref(
                                "product.product_delivery_02"
                            ).id,
                            "account_id": self.account.id,
                            "name": "Producto de prueba",
                            "quantity": 1.0,
                            "price_unit": 100.0,
                            "tax_ids": [(6, 0, self.tax.ids)],
                        },
                    )
                ],
            }
        )
        self.move.refresh()
        self.efact_update_type = self.env.ref(
            "l10n_es_facturae_efact.facturae_efact_update_exchange_type"
        )
        self.backend = self.env.ref("l10n_es_facturae_efact.efact_backend")
        self.backend.storage_id.backend_type = "filesystem"

    def test_constrain_facturae_code_01(self):
        with self.assertRaises(exceptions.ValidationError):
            self.partner.facturae_efact_code = False

    def test_constrain_facturae_code_02(self):
        with self.assertRaises(exceptions.ValidationError):
            self.partner.facturae_efact_code = "1"

    def test_constrain_facturae(self):
        with self.assertRaises(exceptions.ValidationError):
            self.partner.facturae = False

    def test_constrain_vat(self):
        with self.assertRaises(exceptions.ValidationError):
            self.partner.vat = False

    def test_constrain_country(self):
        with self.assertRaises(exceptions.ValidationError):
            self.partner.country_id = False

    def test_constrain_state(self):
        with self.assertRaises(exceptions.ValidationError):
            self.partner.state_id = False

    def test_efact_sending(self):
        self.move.with_context(force_edi_send=True).post()
        self.move.refresh()
        self.assertTrue(self.move.exchange_record_ids)
        exchange_record = self.move.exchange_record_ids
        self.assertEqual(exchange_record.edi_exchange_state, "output_pending")
        exchange_record.backend_id.exchange_send(exchange_record)
        self.assertEqual(exchange_record.edi_exchange_state, "output_sent")
        self.backend.storage_id.add(
            os.path.join("statout", exchange_record.exchange_filename + "@001"),
            bytes(
                tools.file_open(
                    "result.xml", subdir="addons/l10n_es_facturae_efact/tests"
                )
                .read()
                .encode("utf-8")
            ),
        )
        self.env["edi.exchange.record"].efact_check_history()
        exchange_record.flush()
        self.assertEqual(exchange_record.external_identifier, "12")
        self.assertFalse(exchange_record.exchange_error)
        self.assertEqual(self.move.l10n_es_facturae_status, "efact-DELIVERED")

    def test_efact_sending_error(self):
        self.move.with_context(force_edi_send=True).post()
        self.move.refresh()
        self.assertTrue(self.move.exchange_record_ids)
        exchange_record = self.move.exchange_record_ids
        self.assertEqual(exchange_record.edi_exchange_state, "output_pending")
        exchange_record.backend_id.exchange_send(exchange_record)
        self.assertEqual(exchange_record.edi_exchange_state, "output_sent")
        self.backend.storage_id.add(
            os.path.join("statout", exchange_record.exchange_filename + "@001"),
            bytes(
                tools.file_open(
                    "result_02.xml", subdir="addons/l10n_es_facturae_efact/tests"
                )
                .read()
                .encode("utf-8")
            ),
        )
        self.env["edi.exchange.record"].efact_check_history()
        exchange_record.flush()
        self.assertEqual(exchange_record.external_identifier, "12")
        self.assertTrue(exchange_record.exchange_error)
