# (c) 2017 Diagram Software S.L.
# (c) 2017 Consultoría Informática Studio 73 S.L.
# (c) 2019 Acysos S.L.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import os

from odoo import _, exceptions, fields, models


class L10nEsAeatCertificate(models.Model):
    _name = "l10n.es.aeat.certificate"
    _description = "AEAT Certificate"

    name = fields.Char()
    state = fields.Selection(
        selection=[("draft", "Draft"), ("active", "Active")],
        default="draft",
    )
    file = fields.Binary(required=True)
    folder = fields.Char(string="Folder Name", required=True)
    date_start = fields.Date(string="Start Date")
    date_end = fields.Date(string="End Date")
    public_key = fields.Char(readonly=True)
    private_key = fields.Char(readonly=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    def load_password_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Insert Password"),
            "res_model": "l10n.es.aeat.certificate.password",
            "view_mode": "form",
            "views": [(False, "form")],
            "target": "new",
        }

    def action_active(self):
        self.ensure_one()
        other_configs = self.search(
            [("id", "!=", self.id), ("company_id", "=", self.company_id.id)]
        )
        for config_id in other_configs:
            config_id.state = "draft"
        self.state = "active"

    def get_certificates(self, company=False):
        if not company:
            company = self.env.user.company_id
        today = fields.Date.today()
        aeat_certificate = self.search(
            [
                ("company_id", "=", company.id),
                ("public_key", "!=", False),
                ("private_key", "!=", False),
                "|",
                ("date_start", "=", False),
                ("date_start", "<=", today),
                "|",
                ("date_end", "=", False),
                ("date_end", ">=", today),
                ("state", "=", "active"),
            ],
            limit=1,
        )
        if aeat_certificate:
            public_crt = aeat_certificate.public_key
            private_key = aeat_certificate.private_key
            # Verify that certificate files from database actually exist
            if not os.path.isfile(public_crt):
                raise exceptions.UserError(
                    _("Error! Public certificate file not found: %s") % public_crt
                )
            if not os.path.isfile(private_key):
                raise exceptions.UserError(
                    _("Error! Private key file not found: %s") % private_key
                )
        else:
            public_crt = self.env["ir.config_parameter"].get_param(
                "l10n_es_aeat_certificate.publicCrt", False
            )
            private_key = self.env["ir.config_parameter"].get_param(
                "l10n_es_aeat_certificate.privateKey", False
            )
            if not public_crt or not private_key:
                raise exceptions.UserError(_("Error! There aren't certificates."))
            # Verify config parameter paths exist (only if not default placeholders)
            # Default paths (/opt/certificates/*) may not exist on fresh installs
            is_default_public = public_crt == "/opt/certificates/publicCert.crt"
            is_default_private = private_key == "/opt/certificates/privateKey.pem"
            if not is_default_public and not os.path.isfile(public_crt):
                raise exceptions.UserError(
                    _(
                        "Error! Public certificate file not found: %s. "
                        "Please configure a valid certificate through "
                        "Settings > AEAT > Certificates"
                    )
                    % public_crt
                )
            if not is_default_private and not os.path.isfile(private_key):
                raise exceptions.UserError(
                    _(
                        "Error! Private key file not found: %s. "
                        "Please configure a valid certificate through "
                        "Settings > AEAT > Certificates"
                    )
                    % private_key
                )
        return public_crt, private_key
