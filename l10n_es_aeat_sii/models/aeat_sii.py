# (c) 2017 Diagram Software S.L.
# (c) 2017 Consultoría Informática Studio 73 S.L.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models, fields, _


class L10nEsAeatSii(models.Model):
    _name = 'l10n.es.aeat.sii'

    name = fields.Char(string="Name")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active')
    ], string="State", default="draft")
    file = fields.Binary(string="File", required=True)
    date_start = fields.Date(string="Start Date")
    date_end = fields.Date(string="End Date")
    public_key = fields.Char(string="Public Key", readonly=True)
    private_key = fields.Char(string="Private Key", readonly=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.user.company_id.id
    )

    @api.multi
    def load_password_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Insert Password'),
            'res_model': 'l10n.es.aeat.sii.password',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(False, 'form')],
            'target': 'new',
        }

    @api.multi
    def action_activate(self):
        self.ensure_one()
        self.search([
            ('id', '!=', self.id),
            ('company_id', '=', self.company_id.id),
        ]).write({'state': 'draft'})
        self.state = 'active'
