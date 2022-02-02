import logging
import pprint

from lxml import etree, objectify
from odoo import _, api, models
from odoo.addons.payment import utils as payment_utils
from odoo.exceptions import UserError, ValidationError
from werkzeug import urls

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'


    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.acquirer_id.provider != 'redsys':
            return res
        res.update(self.acquirer_id.redsys_form_generate_values(processing_values))
        res.update({"Ds_Sermepa_Url": self.acquirer_id.redsys_get_form_action_url()})
        return res
