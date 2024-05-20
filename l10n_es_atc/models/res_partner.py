# Copyright 2018 PESOL - Angel Moya <info@pesol.es>
# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def get_view(self, view_id=None, view_type="form", **options):
        res = super().get_view(view_id=view_id, view_type=view_type, **options)
        if view_type == "form":
            doc = etree.XML(res["arch"])
            aeat_page = doc.xpath("//page[@id='aeat']")
            if aeat_page:
                aeat_page = aeat_page[0]
                aeat_page.attrib["string"] = "%s / ATC" % aeat_page.attrib.get(
                    "string", ""
                )
                res["arch"] = etree.tostring(doc)
        return res
