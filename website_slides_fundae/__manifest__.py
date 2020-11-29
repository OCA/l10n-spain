# Copyright (C) 2020 C2i Change 2 improve (<http://c2i.es>).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Gestión de formaciones bonificables para FUNDAE",
    "version": "14.0.1.0.0",
    "summary": "Gestión de formaciones bonificables para FUNDAE.",
    "author": "C2i Change 2 improve, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "category": "Localization/Europe",
    "depends": [
        "website_slides",
        "website_slides_forum",
        "website_slides_survey",
        "website_event",
    ],
    "data": [
        "security/ir.model.access.csv",
        "templates/view_portal_templates.xml",
        "templates/website_slides_templates_course.xml",
        "templates/website_slides_templates_lesson.xml",
        "views/slide_channel.xml",
        "views/slide_channel_partner.xml",
        "views/slide_channel_group.xml",
        "views/slide_channel_forum.xml",
        "views/slide_slide.xml",
    ],
    "auto_install": False,
    "installable": True,
}
