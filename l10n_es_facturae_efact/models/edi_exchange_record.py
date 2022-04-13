# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)

try:
    from paramiko.client import SSHClient
except (ImportError, IOError) as err:
    _logger.info(err)
statout_path = "/statout"


class EdiExchangeRecord(models.Model):
    _inherit = "edi.exchange.record"

    def efact_check_history(self):
        efact = self.env.ref("l10n_es_facturae_efact.efact_backend")
        ICP = self.env["ir.config_parameter"].sudo()
        connection = SSHClient()
        connection.load_system_host_keys()
        connection.connect(
            ICP.get_param("account.invoice.efact.server", default=None),
            port=int(ICP.get_param("account.invoice.efact.port", default=None)),
            username=ICP.get_param("account.invoice.efact.user", default=None),
            password=ICP.get_param("account.invoice.efact.password", default=None),
        )
        sftp = connection.open_sftp()
        path = sftp.normalize(".")
        sftp.chdir(path + statout_path)
        attrs = sftp.listdir_attr(".")
        attrs.sort(key=lambda attr: attr.st_atime)
        to_remove = []
        for attr in attrs:
            file = sftp.open(attr.filename)
            datas = file.read()
            file.close()
            update_record = efact.create_record(
                "l10n_es_facturae_efact_update",
                {
                    "edi_exchange_state": "input_received",
                    "exchange_filename": attr.filename,
                },
            )
            update_record._set_file_content(datas)
            efact.with_delay().exchange_process(update_record)
            to_remove.append(attr.filename)
        for filename in to_remove:
            sftp.remove(filename)
        sftp.close()
        connection.close()
