# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import models, api, exceptions, _, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    facturae_efact_code = fields.Char(string='e.Fact code')

    @api.constrains('facturae', 'vat', 'country_id', 'state_id',
                    'invoice_integration_method_ids', 'facturae_efact_code')
    def constrain_efact(self):
        efact = self.env.ref('l10n_es_facturae_efact.integration_efact')
        for record in self.filtered(
                lambda x: efact in x.invoice_integration_method_ids):
            if not record.facturae:
                raise exceptions.ValidationError(
                    _('Facturae must be selected in order to send to e.Fact')
                )
            if not record.vat:
                raise exceptions.ValidationError(
                    _('Vat must be defined in order to send to e.Fact'))
            if not record.country_id:
                raise exceptions.ValidationError(
                    _('Country must be defined in order to send to e.Fact'))
            if record.country_id.code_alpha3 == 'ESP':
                if not record.state_id:
                    raise exceptions.ValidationError(
                        _('State must be defined in Spain in order to '
                          'send to e.Fact'))
            if not record.facturae_efact_code or len(
                    record.facturae_efact_code) != 22:
                raise exceptions.ValidationError(
                    _('e.Fact code must be correctly defined'))
