# Copyright 2020 ForgeFlow
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging

from openupgradelib import openupgrade  # pylint: disable=W7936

_logger = logging.getLogger("aeat.vat.book")


def link_invoices(cr):
    _logger.info("vat book: adding relation to account move")
    cr.execute(
        """
    UPDATE l10n_es_vat_book_line vbl0
    SET move_id = am.id
    FROM l10n_es_vat_book_line vbl
    INNER JOIN account_invoice ai ON vbl.invoice_id = ai.id
    INNER JOIN account_move_line aml ON aml.invoice_id = ai.id
    INNER JOIN account_move am ON aml.move_id = am.id
    WHERE vbl.id = vbl0.id
    """
    )


@openupgrade.migrate()
def migrate(env, version):
    link_invoices(env.cr)
