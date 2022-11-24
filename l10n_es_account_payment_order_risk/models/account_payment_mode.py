from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class AccountPaymentMode(models.Model):
    _inherit = "account.payment.mode"

    def _domain_discounted_effects_id(self):
        group = self.env.ref("l10n_es.account_group_4311").id
        return [("group_id", "=", group)]

    def _domain_debit_discounted_effects_id(self):
        group = self.env.ref("l10n_es.account_group_5208").id
        return [("group_id", "=", group)]

    cancel_risk = fields.Boolean(
        string="Cancel risk",
        help="If checked, it indicates that this mode of payment is only for "
        "the cancellation of accounting risk",
        copy=False,
    )
    control_risk = fields.Boolean(
        string="Control risk",
        help="If checked, it indicates that this payment method has risk " "control",
        copy=False,
    )
    discounted_commercial_effects_id = fields.Many2one(
        string="Discounted commercial effects",
        comodel_name="account.account",
        domain=lambda self: self._domain_discounted_effects_id(),
        copy=False,
    )
    debit_discounted_effects_id = fields.Many2one(
        string="Dues for discounted effects",
        comodel_name="account.account",
        domain=lambda self: self._domain_debit_discounted_effects_id(),
        copy=False,
    )

    @api.onchange("cancel_risk", "control_risk", "company_id")
    def _onchange_payment_risk(self):
        if self.cancel_risk:
            self.control_risk = False
        elif self.control_risk:
            self.cancel_risk = False
        else:
            self.discounted_commercial_effects_id = False
            self.debit_discounted_effects_id = False

    @api.constrains("cancel_risk", "control_risk", "company_id")
    def _check_payment_risk(self):
        for payment in self:
            if payment.cancel_risk and payment.control_risk:
                raise ValidationError(
                    _("Risk control and cancel risk cannot be both checked")
                )
            elif payment.control_risk or payment.cancel_risk:
                if not payment.discounted_commercial_effects_id:
                    raise ValidationError(
                        _("Discounted commercial effects is not checked")
                    )
                elif not payment.debit_discounted_effects_id:
                    raise ValidationError(
                        _("Dues for discounted effects is not checked")
                    )
