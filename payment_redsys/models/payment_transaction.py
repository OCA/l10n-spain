# Copyright 2016-2017 Tecnativa - Sergio Teruel
# Copyright 2019 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2020 Tecnativa - João Marques
# Copyright 2023 Planesnet - Luis Planes, Laia Espinosa, Raul Solana
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import json
import logging
import urllib

from odoo import _, api, fields, models
from odoo.tools import config

from odoo.addons.payment.models.payment_provider import ValidationError

_logger = logging.getLogger(__name__)


class TxRedsys(models.Model):
    _inherit = "payment.transaction"

    redsys_txnid = fields.Char("Transaction ID")

    def merchant_params_json2dict(self, data):
        parameters = data.get("Ds_MerchantParameters", "")
        return json.loads(base64.b64decode(parameters).decode())

    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------

    @api.model
    def _get_tx_from_notification_data(self, provider, data):
        """Given a data dict coming from redsys, verify it and
        find the related transaction record."""
        tx = super()._get_tx_from_notification_data(provider, data)
        if provider != "redsys":
            return tx

        parameters = data.get("Ds_MerchantParameters", "")
        parameters_dic = json.loads(base64.b64decode(parameters).decode())
        reference = urllib.parse.unquote(parameters_dic.get("Ds_Order", ""))
        pay_id = parameters_dic.get("Ds_AuthorisationCode")
        shasign = data.get("Ds_Signature", "").replace("_", "/").replace("-", "+")
        test_env = config["test_enable"]
        if not reference or not pay_id or not shasign:
            error_msg = (
                "Redsys: received data with missing reference"
                " (%s) or pay_id (%s) or shashign (%s)" % (reference, pay_id, shasign)
            )
            if not test_env:
                _logger.info(error_msg)
                raise ValidationError(error_msg)
        tx = self.search([("reference", "=", reference)])
        if not tx or len(tx) > 1:
            error_msg = "Redsys: received data for reference %s" % (reference)
            if not tx:
                error_msg += "; no order found"
            else:
                error_msg += "; multiple order found"
            _logger.info(error_msg)
            raise ValidationError(error_msg)
        if tx and not test_env:
            # verify shasign
            shasign_check = tx.provider_id.sign_parameters(
                tx.provider_id.redsys_secret_key, parameters
            )
            if shasign_check != shasign:
                error_msg = (
                    "Redsys: invalid shasign, received %s, computed %s, "
                    "for data %s" % (shasign, shasign_check, data)
                )
                _logger.info(error_msg)
                raise ValidationError(error_msg)
        return tx

    @api.model
    def _get_redsys_state(self, status_code):
        if 0 <= status_code <= 100:
            return "done"
        elif status_code <= 203:
            return "pending"
        elif 912 <= status_code <= 9912:
            return "cancel"
        else:
            return "error"

    def _process_notification_data(self, data):
        super()._process_notification_data(data)
        if self.provider_code != "redsys":
            return

        params = self.merchant_params_json2dict(data)
        status_code = int(params.get("Ds_Response", "29999"))
        state = self._get_redsys_state(status_code)

        vals = {
            "state": state,
            "redsys_txnid": params.get("Ds_AuthorisationCode"),
            "create_date": fields.Datetime.now(),
        }

        state_message = ""
        feedback_error = False
        if state == "done":
            vals["state_message"] = _("Ok: %s") % params.get("Ds_Response")
            self._set_done()
            self._finalize_post_processing()
        elif state == "pending":  # 'Payment error: code: %s.'
            state_message = _("Error: %(status_code)s (%(error_code)s)")
            self._set_pending()
        elif state == "cancel":  # 'Payment error: bank unavailable.'
            state_message = _("Bank Error: %(status_code)s (%(error_code)s)")
            self._set_canceled()
        else:
            state_message = _(
                "Redsys: feedback error: %(status_code)s (%(error_code)s)"
            )
            self._set_error(state_message)
            feedback_error = True
        if state_message:
            vals["state_message"] = state_message % {
                "status_code": params.get("Ds_Response"),
                "error_code": params.get("Ds_ErrorCode"),
            }
            if state == "error":
                _logger.warning(vals["state_message"])
            if feedback_error:
                self._set_error(state_message)
        self.write(vals)

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != "redsys":
            return res
        redsys_values = dict(processing_values)
        merchant_parameters = self.provider_id._prepare_merchant_parameters(
            processing_values
        )
        redsys_values.update(
            {
                "api_url": self.provider_id._redsys_get_api_url(),
                "Ds_SignatureVersion": str(self.provider_id.redsys_signature_version),
                "Ds_MerchantParameters": merchant_parameters,
                "Ds_Signature": self.provider_id.sign_parameters(
                    self.provider_id.redsys_secret_key, merchant_parameters
                ),
            }
        )
        return redsys_values
