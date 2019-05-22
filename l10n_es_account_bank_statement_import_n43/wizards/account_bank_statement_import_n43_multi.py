# Copyright 2019 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

try:
    import chardet
except ImportError:
    _logger.warning(
        "chardet library not found,  please install it "
        "from http://pypi.python.org/pypi/chardet"
    )


class AccountBankStatementImportN43Multi(models.TransientModel):
    _name = 'account.bank.statement.import.n43.multi'

    data_file = fields.Binary(
        string='Bank Statement File', required=True,
        help='Get you bank statements in electronic format from your bank and '
             'select them here.')
    filename = fields.Char()

    def _get_journal(self, account, n43):
        return self.env['account.journal'].search([
            ('n43_identifier', '=', account)
        ], limit=1)

    @api.multi
    def doit(self):
        self.ensure_one()
        n43_multi = self._check_n43(base64.b64decode(self.data_file))
        for account in n43_multi:
            n43 = n43_multi[account]
            journal = self._get_journal(account, n43)
            self.env['account.bank.statement.import'].create({
                'filename': self.filename,
                'data_file': base64.b64encode(n43['file'].encode(
                    self._get_common_file_encodings()[0])),
            }).with_context(journal_id=journal.id).import_file()
        return {}

    @api.model
    def _get_common_file_encodings(self):
        return self.env[
            'account.bank.statement.import'
        ]._get_common_file_encodings()

    def _check_n43(self, data_file):
        # We'll try to decode with the encoding detected by chardet first
        # otherwise, we'll try with another common encodings until success
        encodings = self._get_common_file_encodings()
        # Try to guess the encoding of the data file
        detected_encoding = chardet.detect(data_file).get('encoding', False)
        if detected_encoding:
            encodings += [detected_encoding]
        while encodings:
            try:
                data_file = data_file.decode(encodings.pop())
                return self._parse(data_file)
            except UnicodeDecodeError:
                pass
        return {}

    @api.model
    def _parse(self, data_file):
        files = {}
        records = 0
        account = False
        for raw_line in data_file.split("\n"):
            records += 1
            if not raw_line.strip():
                continue
            code = raw_line[0:2]
            if code == '11':
                account = raw_line[2:20]
            elif code == '22':
                pass
            elif code == '23':
                pass
            elif code == '24':
                pass
            elif code == '33':
                account = raw_line[2:20]
            elif code == '88':
                registros = int(raw_line[20:26])
                # File level checks
                # Some banks (like Liderbank) are informing this record number
                # including the record 88, so checking this with the absolute
                # difference allows to bypass the error
                if (abs(records - registros) > 1):  # pragma: no cover
                    raise ValidationError(
                        _("Number of records doesn't match with the defined "
                          "in the last record."))
                continue
            elif ord(raw_line[0]) == 26:  # pragma: no cover
                # CTRL-Z (^Z), is often used as an end-of-file marker in DOS
                continue
            else:  # pragma: no cover
                raise ValidationError(
                    _('Record type %s is not valid.') % raw_line[0:2])
            if account not in files:
                files[account] = {
                    'file': '',
                    'lines': 0,
                }
            files[account]['file'] += raw_line + '\n'
            files[account]['lines'] += 1
        result = {}
        for account in files:
            files[account]['file'] += '88999999999999999999%06d' % files[
                account]['lines']
            if files[account]['lines'] > 2:
                result[account] = files[account]
        return result
