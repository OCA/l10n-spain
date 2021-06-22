# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import os

from odoo import models

_logger = logging.getLogger(__name__)


class EdiExchangeRecord(models.Model):
    _inherit = "edi.exchange.record"

    def efact_check_history(self):
        efact = self.env.ref("l10n_es_facturae_efact.efact_backend")
        storage = efact.storage_id
        files = storage.list_files(efact.input_dir_pending)
        for file in files:
            file_path = os.path.join(efact.input_dir_pending, file)
            datas = storage.get(file_path)
            update_record = efact.create_record(
                "l10n_es_facturae_efact_update",
                {"edi_exchange_state": "input_received", "exchange_filename": file},
            )
            update_record._set_file_content(datas)
            efact.storage_id.delete(file_path)
            efact.with_delay().exchange_process(update_record)
