from odoo import fields, models


class SubscriptionRequest(models.Model):
    _inherit = "subscription.request"

    vat = fields.Char(
        string="Tax ID",
        help="""
        The Tax Identification Number. Complete it if the contact is subjected to
        government taxes. Used in some legal statements."
        """,
    )

    def get_partner_vals(self):
        vals = super(SubscriptionRequest, self).get_partner_vals()
        vals["vat"] = self.vat
        return vals

    def get_required_field(self):
        req_fields = super(SubscriptionRequest, self).get_required_field()[:]
        req_fields.append("vat")

        return req_fields

    def _get_partner_domain(self):
        if self.vat:
            return [("vat", "=", self.vat)]
        else:
            return None
