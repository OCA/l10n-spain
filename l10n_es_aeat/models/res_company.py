# Copyright 2019-2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models, fields
from odoo.tools import ormcache


class ResCompany(models.Model):
    _inherit = "res.company"

    tax_agency_id = fields.Many2one(
        'aeat.tax.agency', string='Tax Agency')

    @api.model
    def create(self, values):
        """Create immediately all the AEAT sequences when creating company."""
        company = super().create(values)
        models = self.env['ir.model'].search([
            ('model', '=like', 'l10n.es.aeat.%.report'),
        ])
        for model in models:
            try:
                self.env[model.model]._register_hook(companies=company)
            except Exception:
                pass
        return company

    @ormcache('tax_template', 'company')
    def _get_tax_id_from_tax_template(self, tax_template, company):
        """Low level cached search for a tax given its tax template and
        company.
        """
        xmlids = self.env['ir.model.data'].search_read([
            ('model', '=', 'account.tax.template'),
            ('res_id', '=', tax_template.id)
        ], ['name', 'module'])
        return xmlids and self.env['ir.model.data'].search([
            ('model', '=', 'account.tax'),
            ('module', '=', xmlids[0]['module']),
            ('name', '=', '{}_{}'.format(company.id, xmlids[0]['name']))
        ]).res_id or False

    def get_taxes_from_templates(self, tax_templates):
        """Return company taxes that match the given tax templates."""
        self.ensure_one()
        tax_ids = []
        for tmpl in tax_templates:
            tax_id = self._get_tax_id_from_tax_template(tmpl, self)
            if tax_id:
                tax_ids.append(tax_id)
        return self.env['account.tax'].browse(tax_ids)
