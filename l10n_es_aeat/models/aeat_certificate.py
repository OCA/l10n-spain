# (c) 2017 Diagram Software S.L.
# (c) 2017 Consultoría Informática Studio 73 S.L.
# (c) 2019 Acysos S.L.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import Encoding

from odoo import _, api, exceptions, fields, models


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
    show_public_key = fields.Boolean(store=False)
    public_key_data = fields.Text(readonly=True, store=False)
    private_key = fields.Char(readonly=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    @api.onchange("show_public_key")
    def onchange_public_key_data(self):
        if not self.show_public_key:
            self.public_key_data = ""
            return
        with open(self.public_key, "rb") as f:
            certificate = x509.load_pem_x509_certificate(
                f.read(), backend=default_backend()
            )
        self.public_key_data = certificate.public_bytes(Encoding.PEM)

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
        else:
            public_crt = self.env["ir.config_parameter"].get_param(
                "l10n_es_aeat_certificate.publicCrt", False
            )
            private_key = self.env["ir.config_parameter"].get_param(
                "l10n_es_aeat_certificate.privateKey", False
            )
        if not public_crt or not private_key:
            raise exceptions.UserError(_("Error! There aren't certificates."))
        return public_crt, private_key
