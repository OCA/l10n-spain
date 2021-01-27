# 2018 Alquemy - Javier de las Heras <jheras@alquemy.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
import os
import csv
import tempfile
from odoo.exceptions import UserError
from odoo import _, api, fields, models
import xlrd
import base64
import io
import xlsxwriter

_logger = logging.getLogger(__name__)


class ImportPurchaseOrder(models.TransientModel):
    _name = "wizard.import.silicie"
    _description = "Wizard Import Silicie"

    file_data = fields.Binary(
        string='File',
        required=True,
    )
    file_name = fields.Char()

    def import_button(self):
        extension = self.csv_validator(self.file_name)
        if not extension:
            raise UserError(
                _("El fichero debe tener extensión .csv, .xls o .xlsx"))
        file_path = tempfile.gettempdir() + '/file' + extension
        data = self.file_data
        f = open(file_path, 'wb')
        f.write(base64.b64decode(data))
        f.close()
        # Transformamos el .csv en .xlsx
        if extension == '.csv':
            file_path = tempfile.gettempdir() + '/file.xlsx'
            csv_data = base64.b64decode(data)
            data_file = io.StringIO(csv_data.decode("utf-8-sig"))
            data_file.seek(0)
            file_reader = []
            csv_reader = csv.reader(data_file, delimiter=';')
            file_reader.extend(csv_reader)

            with xlsxwriter.Workbook(file_path) as workbook:
                worksheet = workbook.add_worksheet()

                for row_num, data in enumerate(file_reader):
                    worksheet.write_row(row_num, 0, data)

        workbook = xlrd.open_workbook(file_path, on_demand=True)
        worksheet = workbook.sheet_by_index(0)
        first_row = []  # The row where we stock the name of the column
        for col in range(worksheet.ncols):
            first_row.append(worksheet.cell_value(0, col))
        # transform the workbook to a list of dictionaries
        archive_lines = []
        for row in range(1, worksheet.nrows):
            elm = {}
            for col in range(worksheet.ncols):
                elm[first_row[col]] = worksheet.cell_value(row, col)

            archive_lines.append(elm)

        self.valid_columns_keys(archive_lines)

        for line in archive_lines:
            move_id = int(line.get('Número Referencia Interno', 0))
            account_number = anti_float(line.get('Número Asiento', ""))
            account_type = anti_float(line.get('Tipo Asiento', ""))
            move = self.env['stock.move'].browse(move_id)
            if move:
                move.silicie_move_number = account_number
                move.silicie_entry_type = account_type
                move.date_send_silicie = fields.datetime.now()

        return

    @api.model
    def valid_columns_keys(self, archive_lines):
        columns = archive_lines[0].keys()
        _logger.warning("columns>> {}".format(columns))
        text = _("Las siguientes columnas no están en el fichero:")
        text2 = text
        if 'Número Asiento' not in columns:
            text += "\n[ Número Asiento ]"
        if 'Tipo Asiento' not in columns:
            text += "\n[ Tipo Asiento ]"
        if 'Número Referencia Interno' not in columns:
            text += "\n[ Número Referencia Interno ]"
        if text != text2:
            raise UserError(text)
        return True

    @api.model
    def csv_validator(self, xml_name):
        name, extension = os.path.splitext(xml_name)
        return extension if extension == '.csv' or \
                            extension == '.xls' or \
                            extension == '.xlsx' else False


def anti_float(value):
    if type(value) == float:
        value = str(int(value)).strip()
    else:
        value = str(value).strip()
    return value
