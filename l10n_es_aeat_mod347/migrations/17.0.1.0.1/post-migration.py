# Copyright 2024 Ángel García de la Chica Herrera <angel.garcia@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    template = env.ref("l10n_es_aeat_mod347.email_template_347")
    for lang_code, _ in env["res.lang"].get_installed():
        translated_subject = template.with_context(lang=lang_code).subject
        new_subject = translated_subject.replace(
            "{{user.company_id.name}}", "{{object.report_id.company_id.name}}"
        )
        template.with_context(lang=lang_code).write({"subject": new_subject})
