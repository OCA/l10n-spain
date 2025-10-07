# Copyright 2025 Factor Libre - Almudena de La Puente
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    cr.execute(
        """UPDATE verifactu_invoice_entry
        SET send_state = 'sent'
        WHERE send_state = 'correct'"""
    )
    cr.execute(
        """UPDATE verifactu_invoice_entry
        SET send_state = 'sent_w_errors'
        WHERE send_state = 'accepted_with_errors'"""
    )
    cr.execute(
        """UPDATE verifactu_invoice_entry_response_line
        SET send_state = 'sent'
        WHERE send_state = 'correct'"""
    )
    cr.execute(
        """UPDATE verifactu_invoice_entry_response_line
        SET send_state = 'sent_w_errors'
        WHERE send_state = 'accepted_with_errors'"""
    )
