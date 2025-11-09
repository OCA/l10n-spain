# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


def migrate(cr, version):
    cr.execute(
        "UPDATE l10n_es_vat_book_line_tax SET deductible_amount = tax_amount "
        "WHERE deductible_amount IS NULL"
    )
