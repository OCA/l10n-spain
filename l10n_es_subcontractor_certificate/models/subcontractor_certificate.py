# Copyright 2014 Domatix Technologies S.L. - Angel Moya
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    certificate_required = fields.Boolean()
    certificate_expiration_aeat = fields.Date(string="AEAT Certificate Expiration")
    certificate_expired_aeat = fields.Boolean(
        string="AEAT Certificate Expirated", compute="_compute_certificate_expired_aeat"
    )
    certificate_expiration_ss = fields.Date(string="SS Certificate Expiration")
    certificate_expired_ss = fields.Boolean(
        string="SS Certificate Expirated", compute="_compute_certificate_expired_ss"
    )

    @api.depends("certificate_expiration_aeat")
    def _compute_certificate_expired_aeat(self):
        for partner in self:
            partner.certificate_expired_aeat = partner.certificate_expiration_aeat and (
                partner.certificate_expiration_aeat < fields.Date.today()
            )

    @api.depends("certificate_expiration_ss")
    def _compute_certificate_expired_ss(self):
        for partner in self:
            partner.certificate_expired_ss = partner.certificate_expiration_ss and (
                partner.certificate_expiration_ss < fields.Date.today()
            )


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.onchange("partner_id", "company_id")
    def onchange_partner_id(self):
        res = super().onchange_partner_id() or {}
        partner = self.partner_id
        if partner:
            if partner.certificate_required:
                if not partner.certificate_expiration_aeat:
                    res["warning"] = {
                        "title": self.env._("Warning!"),
                        "message": self.env._(
                            "The AEAT certificate is required and "
                            "expiration date is not set"
                        ),
                    }
                elif partner.certificate_expired_aeat:
                    res["warning"] = {
                        "title": self.env._("Warning!"),
                        "message": self.env._(
                            "The AEAT certificate for this supplier has expired"
                        ),
                    }
                elif not partner.certificate_expiration_ss:
                    res["warning"] = {
                        "title": self.env._("Warning!"),
                        "message": self.env._(
                            "The SS certificate is required and "
                            "expiration date is not set"
                        ),
                    }
                elif partner.certificate_expired_ss:
                    res["warning"] = {
                        "title": self.env._("Warning!"),
                        "message": self.env._(
                            "The SS certificate for this supplier has expired"
                        ),
                    }
        return res


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.onchange("partner_id", "company_id")
    def _onchange_partner_id(self):
        res = super()._onchange_partner_id() or {}
        if self.move_type == "in_invoice" and self.partner_id:
            partner = self.partner_id
            if partner.certificate_required:
                if not partner.certificate_expiration_aeat:
                    res["warning"] = {
                        "title": self.env._("Warning!"),
                        "message": self.env._(
                            "The AEAT certificate is required and "
                            "expiration date is not set"
                        ),
                    }
                elif partner.certificate_expired_aeat:
                    res["warning"] = {
                        "title": self.env._("Warning!"),
                        "message": self.env._(
                            "The AEAT certificate for this supplier has expired"
                        ),
                    }
                elif not partner.certificate_expiration_ss:
                    res["warning"] = {
                        "title": self.env._("Warning!"),
                        "message": self.env._(
                            "The SS certificate is required and "
                            "expiration date is not set"
                        ),
                    }
                elif partner.certificate_expired_ss:
                    res["warning"] = {
                        "title": self.env._("Warning!"),
                        "message": self.env._(
                            "The SS certificate for this supplier has expired"
                        ),
                    }
        return res
