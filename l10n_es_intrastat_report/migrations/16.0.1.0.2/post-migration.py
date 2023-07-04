# -*- coding: utf-8 -*-
from openupgradelib import openupgrade

@openupgrade.migrate(use_env=True)
def migrate(env, version):
    """ Putting l10n_es_intrastat.... all tables data
    into new tables create with module v16
    """
    env.cr.execute("""
        DROP TABLE IF EXISTS intrastat_product_computation_line;
        DROP TABLE IF EXISTS intrastat_product_declaration_line;
        DROP TABLE IF EXISTS intrastat_product_declaration;

        ALTER TABLE l10n_es_intrastat_product_computation_line RENAME TO intrastat_product_computation_line;
        ALTER TABLE l10n_es_intrastat_product_declaration_line RENAME TO intrastat_product_declaration_line;
        ALTER TABLE l10n_es_intrastat_product_declaration RENAME TO intrastat_product_declaration;
    """)

