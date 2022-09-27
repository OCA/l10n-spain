# Copyright 2021 Tecnativa- Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import json

from lxml import etree

from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    thirdparty_invoice = fields.Boolean(string="Third-party invoice", copy=False)

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        """Thirdparty fields are added to the form view only if they don't exist
        previously (l10n_es_aeat_sii_oca addon also has the same field names).
        """
        res = super().fields_view_get(
            view_id=view_id,
            view_type=view_type,
            toolbar=toolbar,
            submenu=submenu,
        )
        if view_type == "form":
            doc = etree.XML(res["arch"])
            node = doc.xpath("//field[@name='thirdparty_invoice']")
            if node:
                return res
            for node in doc.xpath("//field[@name='type']"):
                attrs = {
                    "invisible": [("type", "not in", ("sale", "purchase"))],
                }
                modifiers = {"invisible": attrs["invisible"]}
                elem = etree.Element(
                    "field",
                    {
                        "name": "thirdparty_invoice",
                        "attrs": str(attrs),
                        "modifiers": json.dumps(modifiers),
                    },
                )
                node.addnext(elem)
            res["arch"] = etree.tostring(doc)
            res["fields"].update(self.fields_get(["thirdparty_invoice"]))
        return res
