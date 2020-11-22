# Copyright (C) 2020 C2i Change 2 improve (<http://c2i.es>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import http
from odoo.http import request


class WebsiteSlidesFundae(http.Controller):
    @http.route(
        '/fundae/<model("slide.channel"):channel_template>',
        type="http",
        auth="user",
        website=True,
    )
    def channel_render(self, channel_template):
        return request.render(
            "website_slides_fundae.channel_template", {"channel": channel_template}
        )
