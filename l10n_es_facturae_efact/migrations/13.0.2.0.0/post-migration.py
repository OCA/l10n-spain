# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
    UPDATE res_partner
    SET l10n_es_facturae_sending_code = 'face'
    WHERE  l10n_es_facturae_sending_code = 'efact'
    """,
    )

    storage = env.ref("l10n_es_facturae_efact.efact_storage", raise_if_not_found=False)
    # In case someone passed through the storage version, we will restore the data
    if storage:
        ICP = env["ir.config_parameter"].sudo()
        ICP.set_param("account.invoice.efact.server", storage.sftp_server)
        ICP.set_param("account.invoice.efact.port", storage.sftp_port)
        ICP.set_param("account.invoice.efact.user", storage.sftp_login)
        ICP.set_param("account.invoice.efact.password", storage.sftp_password)
    cron_job = env.ref(
        "l10n_es_facturae_efact.update_efact_job", raise_if_not_found=False
    )
    if cron_job:
        cron_job.write(
            {"model_id": env.ref("l10n_es_facturae_efact.model_edi_exchange_record")}
        )
