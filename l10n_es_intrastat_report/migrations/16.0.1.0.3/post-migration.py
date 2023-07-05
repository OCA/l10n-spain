from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    """Putting l10n_es_intrastat.... all tables data
    into new tables create with module v16
    """
    env.cr.execute(
        """
        update account_fiscal_position as afp set intrastat = null;
    """
    )
