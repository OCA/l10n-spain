# Copyright (C) 2020 C2i Change 2 improve (<http://c2i.es>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from werkzeug import urls

from odoo import _, api, fields, models


class Slide(models.Model):
    _inherit = "slide.slide"

    slide_type = fields.Selection(
        selection_add=[
            ("teleconference", "Videoconferencia"),
            ("quiz",),
            ("certification",),
        ],
        ondelete={
            "teleconference": "set default",
            "quiz": "set default",
            "certification": "set default",
        },
    )

    nbr_teleconference = fields.Integer(
        "Número de videoconferencias", compute="_compute_slides_statistics", store=True
    )

    @api.onchange("url")
    def _on_change_url(self):
        self.ensure_one()
        if self.slide_type == "teleconference":
            res = self._clean_website(self.url)
        elif self.url:
            res = self._parse_document_url(self.url)
            if res.get("error"):
                raise Warning(
                    _(
                        "Could not fetch data from url. "
                        "Document or access right not available:\n%s"
                    )
                    % res["error"]
                )
            values = res["values"]
            if not values.get("document_id"):
                raise Warning(_("Please enter valid Youtube or Google Doc URL"))
            for key, value in values.items():
                self[key] = value

    def _clean_website(self, url):
        link = urls.url_parse(url)
        if not link.scheme:
            if not link.netloc:
                link = link.replace(netloc=link.path, path="")
            url = link.replace(scheme="http").to_url()
        return url

    @api.model
    def _parse_document_url(self, url, only_preview_fields=False):
        if self.slide_type == "teleconference":
            res = self._clean_website(url)
        else:
            res = super(Slide, self)._parse_document_url(url)
        return res
