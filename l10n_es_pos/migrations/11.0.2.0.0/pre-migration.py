# Copyright 2018 David Vidal <david.vidal@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    if not version:
        return
    # Move simplified invoice info to pos_reference field.
    cr.execute("""
        UPDATE pos_order SET
            pos_reference = l10n_es_simplified_invoice_number,
            is_l10n_es_simplified_invoice = TRUE
        WHERE (l10n_es_simplified_invoice_number IS NOT NULL OR
               l10n_es_simplified_invoice_number <> '')
    """)
