# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class VatNumberXlsx(models.AbstractModel):
    _inherit = "report.l10n_es_vat_book.l10n_es_vat_book_xlsx"

    def fill_issued_row_data(
        self, sheet, row, line, tax_line, with_total, draft_export
    ):
        """Add final number if move has is_invoice_summary."""
        res = super().fill_issued_row_data(
            sheet, row, line, tax_line, with_total, draft_export
        )
        if line.move_id.is_invoice_summary:
            sheet.write("D" + str(row), line.move_id.sii_invoice_summary_start)
            sheet.write("E" + str(row), line.move_id.sii_invoice_summary_end)
        return res
