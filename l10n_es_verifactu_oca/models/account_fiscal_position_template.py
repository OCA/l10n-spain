from odoo import api, fields, models


class AccountFiscalPositionTemplate(models.Model):
    _inherit = "account.fiscal.position.template"

    verifactu_tax_key = fields.Selection(
        selection="_get_verifactu_tax_keys", string="VERI*FACTU tax key"
    )
    verifactu_registration_key = fields.Many2one(
        comodel_name="verifactu.registration.key",
        string="VERI*FACTU registration key",
        ondelete="restrict",
    )

    @api.model
    def _get_verifactu_tax_keys(self):
        return self.env["account.fiscal.position"]._get_verifactu_tax_keys()
