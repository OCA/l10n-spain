# Copyright 2016-2017 Tecnativa - Sergio Teruel
# Copyright 2023 Planesnet - Luis Planes, Laia Espinosa, Raul Solana
# Copyright 2025 Acysos S.L. - Ignacio Ibeas <ignacio@acysos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import json
import logging
from unittest import mock

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import RedsysCommon

_logger = logging.getLogger(__name__)


@tagged("post_install", "-at_install")
class RedsysTest(RedsysCommon):
    def _get_expected_values(self, reference=None):
        if not reference:
            reference = self.reference
        values = {
            "reference": reference,
            "amount": self.amount,
        }
        rendering_values = self._get_tx(reference)._get_specific_rendering_values(
            values
        )
        return {
            "data_set": None,
            "Ds_SignatureVersion": rendering_values["Ds_SignatureVersion"],
            "Ds_MerchantParameters": rendering_values["Ds_MerchantParameters"],
            "Ds_Signature": rendering_values["Ds_Signature"],
        }

    def test_compatible_providers(self):
        providers = self.env["payment.provider"]._get_compatible_providers(
            partner_id=self.partner.id,
            amount=0,
            currency_id=self.currency_euro.id,
            company_id=self.company.id,
        )
        self.assertIn(self.redsys, providers)

    def test_redirect_form_values(self):
        tx = self._create_transaction(flow="redirect", reference="Valid transaction")
        expected_values = self._get_expected_values(tx.reference)

        with mute_logger("odoo.addons.payment.models.payment_transaction"):
            processing_values = tx._get_processing_values()

        form_info = self._extract_values_from_html_form(
            processing_values["redirect_form_html"]
        )

        self.assertEqual(
            form_info["action"], "https://sis-t.redsys.es:25443/sis/realizarPago/"
        )
        self.assertDictEqual(
            expected_values,
            form_info["inputs"],
            "Redsys: invalid inputs specified in the redirect form.",
        )

    def _prepare_post_data(self, values):
        # Simulate data received from Redsys
        merchant_parameters = self.redsys._url_encode64(json.dumps(values))

        return {
            "Ds_MerchantParameters": merchant_parameters,
            "Ds_Signature": self.redsys.sign_parameters(
                self.redsys.redsys_secret_key, merchant_parameters.decode("utf8")
            ),
        }

    def test_process_notification_data(self):
        tx = self._create_transaction(flow="redirect", reference="Valid transaction")
        values = {
            "Ds_Order": tx.reference,
            "Ds_AuthorisationCode": "999999",
            "Ds_Response": "100",
        }
        post_data = self._prepare_post_data(values)

        tx = self.env["payment.transaction"]._get_tx_from_notification_data(
            "redsys", post_data
        )
        tx._process_notification_data(post_data)
        self.assertEqual(
            tx.state, "done", "Redsys: validation did not put tx into done state"
        )

    def test_unknown_transaction(self):
        # typical data posted by Redsys after client has successfully paid
        # unknown transaction
        values = {
            "Ds_Order": "unknown transaction",
            "Ds_AuthorisationCode": "999999",
        }
        post_data = self._prepare_post_data(values)
        with self.assertRaises(ValidationError):
            self.env["payment.transaction"]._handle_notification_data(
                "redsys", post_data
            )

    def test_feedback_processing(self):
        # typical data posted by Redsys after client has successfully paid

        # redsys not authorisation code
        values = {
            "Ds_Order": "Valid transaction",
            "Ds_AuthorisationCode": "",
        }
        post_data = self._prepare_post_data(values)
        with self.assertRaises(ValidationError):
            self.env["payment.transaction"]._handle_notification_data(
                "redsys", post_data
            )

        # Valid transaction. status: done
        tx = self._create_transaction(flow="redirect", reference="Valid transaction")
        values = {
            "Ds_Order": tx.reference,
            "Ds_AuthorisationCode": "999999",
            "Ds_Response": "100",
        }
        post_data = self._prepare_post_data(values)

        tx._handle_notification_data("redsys", post_data)
        self.assertEqual(
            tx.state, "done", "Redsys: validation did not put tx into done state"
        )

        # No valid card transaction. status: pending
        tx = self._create_transaction(flow="redirect", reference="Pending transaction")
        values = {
            "Ds_Order": tx.reference,
            "Ds_AuthorisationCode": "999999",
            "Ds_Response": "203",
        }
        post_data = self._prepare_post_data(values)
        tx._handle_notification_data("redsys", post_data)
        self.assertEqual(tx.state, "pending", "Redsys: pending transaction status")

        # Cancel status
        tx = self._create_transaction(flow="redirect", reference="Cancel transaction")
        values = {
            "Ds_Order": tx.reference,
            "Ds_AuthorisationCode": "999999",
            "Ds_Response": "913",
        }
        post_data = self._prepare_post_data(values)
        tx._handle_notification_data("redsys", post_data)
        self.assertEqual(tx.state, "cancel", "Redsys: 913-9912 generic invalid card")

        # Error transction status
        tx = self._create_transaction(flow="redirect", reference="Error transaction")
        values = {
            "Ds_Order": tx.reference,
            "Ds_AuthorisationCode": "999999",
            "Ds_Response": "9999",
        }
        post_data = self._prepare_post_data(values)
        tx._handle_notification_data("redsys", post_data)
        self.assertEqual(tx.state, "error", "Redsys: response error")

    def test_redsys_urls(self):
        """Test that Redsys URLs are retrieved from system parameters"""
        # Set system parameters
        self.env["ir.config_parameter"].set_param(
            "payment_redsys.url_authorize_prod", "https://prod.example.com"
        )
        self.env["ir.config_parameter"].set_param(
            "payment_redsys.url_authorize_test", "https://test.example.com"
        )

        # Create a payment record to call the method
        payment = self.env["account.payment"].create(
            {
                "amount": 10.0,
                "payment_type": "inbound",
                "partner_type": "customer",
                "partner_id": self.partner.id,
            }
        )

        # Verify prod URL
        prod_url = payment._get_redsys_rest_urls("prod")
        self.assertEqual(prod_url, "https://prod.example.com")

        # Verify test URL
        test_url = payment._get_redsys_rest_urls("test")
        self.assertEqual(test_url, "https://test.example.com")

    def test_redsys_authorize(self):
        """Test Redsys authorization flow"""
        # Enable Redsys authorization on provider
        self.redsys.redsys_transaction_type = "1"
        self.redsys.redsys_merchant_code = "123456789"
        self.redsys.redsys_terminal = "1"
        self.redsys.redsys_secret_key = "sq7HjrUOBfKmC576ILgskD5srU870gJ8"

        # Create payment
        # We need to find or create the payment method line for Redsys
        # We need to find or create the payment method line for Redsys
        # and the current journal. Use the first bank journal of the company.
        journal = self.env["account.journal"].search(
            [("type", "=", "bank"), ("company_id", "=", self.company.id)],
            limit=1,
        )
        payment_method_id = self.env.ref("payment_redsys.payment_method_redsys").id
        payment_method_line = self.env["account.payment.method.line"].search(
            [
                ("journal_id", "=", journal.id),
                ("payment_method_id", "=", payment_method_id),
            ],
            limit=1,
        )
        if not payment_method_line:
            payment_method_line = self.env["account.payment.method.line"].create(
                {
                    "name": "Redsys",
                    "payment_method_id": payment_method_id,
                    "journal_id": journal.id,
                    "payment_provider_id": self.redsys.id,
                    "company_id": self.company.id,
                }
            )

        _logger.info(
            "Created/Found Payment Method Line: %s (Journal: %s, Check: %s)",
            payment_method_line.id,
            journal.id,
            payment_method_line.journal_id.id,
        )

        payment = self.env["account.payment"].create(
            {
                "amount": 100.0,
                "payment_type": "inbound",
                "partner_type": "customer",
                "partner_id": self.partner.id,
                "payment_method_line_id": payment_method_line.id,
                "journal_id": journal.id,
            }
        )
        # Link a transaction to the payment to trigger compute
        # In the real flow, the transaction is created when the user pays.
        # But _compute_is_redsys_auth depends on payment_transaction_id.provider_id
        # We need to manually link a transaction or mock it.
        # Let's create a transaction and link it.
        transaction = self._create_transaction(flow="redirect", reference="Test Auth")
        payment.payment_transaction_id = transaction

        # 1. Test _compute_is_redsys_auth
        self.assertTrue(payment.is_redsys_auth)

        # 2. Test _change_redsys_auth_amount (depends on amount_total)
        # Default amount_total is same as amount for simple payments
        self.assertEqual(payment.redsys_auth_amount, 100.0)
        payment.amount = 200.0
        # Trigger recompute or manually call if needed, but depends should handle it
        payment.flush_recordset()
        self.assertEqual(payment.redsys_auth_amount, 200.0)

        # 3. Test redsys_authorize_amount Validation Errors

        # Case: Wrong transaction type
        self.redsys.redsys_transaction_type = "0"
        with self.assertRaisesRegex(ValidationError, "Transaction type must be '1'"):
            payment.redsys_authorize_amount()
        self.redsys.redsys_transaction_type = "1"

        # Case: Amount 0
        payment.redsys_auth_amount = 0.0
        with self.assertRaisesRegex(
            ValidationError,
            "Redsys: Authorization amount must be set before authorizing.",
        ):
            payment.redsys_authorize_amount()
        payment.redsys_auth_amount = 200.0

        # Case: Already done
        payment.redsys_auth_done = True
        with self.assertRaisesRegex(ValidationError, "Authorization already done"):
            payment.redsys_authorize_amount()
        payment.redsys_auth_done = False

        # 4. Test redsys_authorize_amount Success
        # Prepare mock response
        response_data = {
            "Ds_AuthorisationCode": "123456",
            "Ds_Response": "0900",
        }
        b64_params = base64.b64encode(json.dumps(response_data).encode()).decode()
        mock_response = {
            "Ds_MerchantParameters": b64_params,
        }

        with mock.patch("requests.post") as mock_post:
            mock_post.return_value.json.return_value = mock_response

            payment.redsys_authorize_amount()

            self.assertTrue(payment.redsys_auth_done)
            self.assertEqual(payment.redsys_auth_txnid, "123456")
            self.assertEqual(payment.state, "posted")

        # 5. Test redsys_authorize_amount Failure (Refused)
        payment.action_draft()  # Reset for next test
        payment.redsys_auth_done = False
        payment.redsys_auth_txnid = False

        response_data_fail = {
            "Ds_AuthorisationCode": "123456",
            "Ds_Response": "0100",  # Error code
        }
        b64_params_fail = base64.b64encode(
            json.dumps(response_data_fail).encode()
        ).decode()
        mock_response_fail = {
            "Ds_MerchantParameters": b64_params_fail,
        }

        with mock.patch("requests.post") as mock_post:
            mock_post.return_value.json.return_value = mock_response_fail

            payment.redsys_authorize_amount()

            self.assertFalse(payment.redsys_auth_done)
            # Should have posted a message
