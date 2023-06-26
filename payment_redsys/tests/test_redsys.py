# Copyright 2016-2017 Tecnativa - Sergio Teruel
# Copyright 2023 Planesnet - Luis Planes, Laia Espinosa, Raul Solana
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging

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
