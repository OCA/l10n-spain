# Copyright 2026 Dixmit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
    UPDATE edi_exchange_type eet
    SET output_template_id = NULL
    FROM ir_model_data data
    WHERE
    data.name = 'edi.facturae_output_template' AND
    data.module = 'l10n_es_facturae_face' AND
    eet.output_template_id = data.res_id
    """,
    )
