# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Base for Spanish TGSS-related models",
    "summary": "Some modules need this to interact with the Spanish TGSS",
    "version": "8.0.1.0.0",
    "category": "Customer Relationship Management",
    "website": "https://grupoesoc.es/",
    "author": u"Grupo ESOC Ingeniería de servicios, S.L., "
              u"Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base",
    ],
    "data": [
        "data/l10n_es_tgss_base.contribution_group.csv",
        "data/l10n_es_tgss_base.professional_category.csv",
        "data/l10n_es_tgss_base.study_level.csv",
        "security/ir.model.access.csv",
        "views/contribution_group.xml",
        "views/professional_category.xml",
        "views/study_level.xml",
    ],
}
