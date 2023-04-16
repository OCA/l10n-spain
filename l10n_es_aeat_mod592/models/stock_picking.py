# Copyright 2023 Nicolás Ramos - (https://binhex.es)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = "stock.picking"

    total_plastic_weight = fields.Float(
        _("Total Weight"),
        store=True,
        readonly=True,
        compute="_depends_invoice_line_ids",
    )
    total_plastic_weight_non_recyclable = fields.Float(
        _("Total Weight no reclyclable"),
        store=True,
        readonly=True,
        compute="_depends_invoice_line_ids",
    )

    @api.depends('invoice_line_ids.product_plastic_tax_weight', 'invoice_line_ids.product_plastic_weight_non_recyclable', 'invoice_line_ids.quantity')
    def _depends_invoice_line_ids(self):
        for move in self:
            plastic_weight = 0.0
            plastic_weight_non_recyclable = 0.0
            for line in move.invoice_line_ids:
                plastic_weight += line.quantity * line.product_plastic_tax_weight
                plastic_weight_non_recyclable += line.quantity * line.product_plastic_weight_non_recyclable
                move.write({
                    'total_plastic_weight': plastic_weight,
                    'total_plastic_weight_non_recyclable': plastic_weight_non_recyclable,
                })

    mod592_mapped = fields.Boolean('Mod592 Mapped', default=False)

    company_plastic_type = fields.Selection([
        ('manufacturer', _('Manufacturer')),
        ('acquirer', _('Acquirer')),
        ('both', _('Both')),
    ], string='Company Plastic Type', compute='_company_id_plastic_type')


    def _company_id_plastic_type(self):
        for company in self:
            if self.company_id:
                company.company_plastic_type = self.company_id.company_plastic_type
            else:
                company.company_plastic_type = self.env.user.company_id.company_plastic_type



