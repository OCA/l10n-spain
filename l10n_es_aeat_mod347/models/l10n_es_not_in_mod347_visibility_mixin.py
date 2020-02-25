# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from lxml import etree
from odoo import api, fields, models
from odoo.osv import orm


class L10nEsMod347VisibilityMixin(models.AbstractModel):
    """Add a computed field to define not_in_mod347 field visibility"""

    _name = 'l10n.es.mod347.visibility.mixin'
    _description = 'L10n Spain mod347 Visibility Mixin'

    is_not_in_mod347_visible = fields.Boolean(
        compute="_compute_is_not_in_mod347_visible"
    )

    @api.depends('company_id')
    def _compute_is_not_in_mod347_visible(self):
        for rec in self:
            rec.is_not_in_mod347_visible = (
                not rec.company_id.country_id
                or rec.company_id.country_id.code == 'ES'
            )

    def fields_view_get(
        self, view_id=None, view_type='form', toolbar=False, submenu=False
    ):
        """set visibility rule for not_in_mod347 field"""
        result = super(L10nEsMod347VisibilityMixin, self).fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu,
        )

        if view_type in ['tree', 'form']:
            doc = etree.XML(result['arch'])
            for node in doc.xpath("//field[@name='not_in_mod347']"):
                elem = etree.Element(
                    'field',
                    {'name': 'is_not_in_mod347_visible', 'invisible': 'True'},
                )
                orm.setup_modifiers(
                    elem,
                    self.fields_get(['is_not_in_mod347_visible'])[
                        'is_not_in_mod347_visible'
                    ],
                )
                node.addprevious(elem)
                node.set(
                    'attrs',
                    '{"invisible": [("is_not_in_mod347_visible", "=", False)]}',
                )
                orm.setup_modifiers(node, result['fields']['not_in_mod347'])
            result['arch'] = etree.tostring(doc, encoding='unicode')
        return result
