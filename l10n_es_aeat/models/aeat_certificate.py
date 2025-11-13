# (c) 2017 Diagram Software S.L.
# (c) 2017 Consultoría Informática Studio 73 S.L.
# (c) 2019 Acysos S.L.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from cryptography.hazmat.primitives.serialization import Encoding

from odoo import api, exceptions, fields, models

_logger = logging.getLogger(__name__)

try:
    import cryptography
    from cryptography import x509

    CRYPTOGRAPHY_VERSION_3 = tuple(map(int, cryptography.__version__.split("."))) >= (
        3,
        0,
    )
    if not CRYPTOGRAPHY_VERSION_3:
        from cryptography.hazmat.backends import default_backend

        def load_pem_x509_certificate(*args, **kwargs):
            return x509.load_pem_x509_certificate(
                *args, **kwargs, backend=default_backend()
            )

    else:
        load_pem_x509_certificate = x509.load_pem_x509_certificate
except (OSError, ImportError) as err:
    _logger.debug(err)


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
    public_key_file = fields.Binary(
        readonly=True,
        store=False,
        attachment=False,
        compute="_compute_public_key",
        groups="l10n_es_aeat.group_account_aeat",
    )
    public_key_filename = fields.Char(
        readonly=True,
        store=False,
        compute="_compute_public_key",
        groups="l10n_es_aeat.group_account_aeat",
    )
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
            certificate = load_pem_x509_certificate(f.read())
        self.public_key_data = certificate.public_bytes(Encoding.PEM)

    def get_public_key_pem(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "target": "self",
            "url": "/web/content/l10n.es.aeat.certificate/"
            f"{self.id}/public_key_file/{self.public_key_filename}?download=true",
        }

    @api.depends("public_key")
    def _compute_public_key(self):
        for record in self:
            if not record.public_key:
                record.public_key_file = False
                record.public_key_filename = False
                continue
            with open(record.public_key, "rb") as f:
                certificate = load_pem_x509_certificate(f.read())
            public_key = certificate.public_bytes(Encoding.PEM)
            record.public_key_filename = f"{record.name}.pem"
            record.public_key_file = public_key

    def load_password_wizard(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Insert Password"),
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
            raise exceptions.UserError(self.env._("Error! There aren't certificates."))
        return public_crt, private_key
