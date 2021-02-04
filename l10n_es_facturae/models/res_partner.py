# © 2015 Omar Castiñeira (Comunitea)
# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, exceptions, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    facturae = fields.Boolean('Factura electrónica')
    facturae_version = fields.Selection([
        ('3_2', '3.2'),
        ('3_2_1', '3.2.1'),
        ('3_2_2', '3.2.2'),
    ])
    organo_gestor = fields.Char('Órgano gestor', size=10)
    unidad_tramitadora = fields.Char('Unidad tramitadora', size=10)
    oficina_contable = fields.Char('Oficina contable', size=10)
    organo_proponente = fields.Char('Órgano proponente', size=10)
    invoice_integration_method_ids = fields.Many2many(
        comodel_name='account.invoice.integration.method',
        string="Integration Methods"
    )
    attach_invoice_as_annex = fields.Boolean()

    def get_facturae_residence(self):
        if not self.country_id:
            return 'E'
        if self.country_id.code == 'ES':
            return 'R'
        for group in self.country_id.country_group_ids:
            if group.name == 'Europe':
                return 'U'
        return 'E'

    @api.constrains('facturae', 'vat', 'state_id', 'country_id')
    def check_facturae(self):
        for record in self:
            if record.facturae:
                if not record.vat:
                    raise exceptions.ValidationError(_('Vat must be defined'))
                if not record.country_id:
                    raise exceptions.ValidationError(
                        _('Country must be defined'))
                if record.country_id.code_alpha3 == 'ESP':
                    if not record.state_id:
                        raise exceptions.ValidationError(
                            _('State must be defined'))
