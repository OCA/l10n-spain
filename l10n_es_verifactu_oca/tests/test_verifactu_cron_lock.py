# Copyright 2026 FactorLibre
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from contextlib import contextmanager
from unittest.mock import patch

import odoo
from odoo.tests import common
from odoo.tests.common import BaseCase
from odoo.tools.misc import mute_logger

from odoo.addons.l10n_es_verifactu_oca.models.verifactu_invoice_entry import (
    VerifactuInvoiceEntry,
)

ADMIN_USER_ID = common.ADMIN_USER_ID


@contextmanager
def environment():
    """Environment with a new committed cursor (needed to reproduce the lock
    contention across two real connections, as core does in test_ir_sequence)."""
    registry = odoo.registry(common.get_db_name())
    with registry.cursor() as cr:
        yield odoo.api.Environment(cr, ADMIN_USER_ID, {})


class TestVerifactuCronLock(BaseCase):
    """The send cron must skip a chaining whose pending entries are locked by
    another process (SELECT ... FOR UPDATE NOWAIT -> SQLSTATE 55P03) instead of
    aborting the whole run."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with environment() as env:
            chaining = env["verifactu.chaining"].create(
                {
                    "name": "TEST LOCK CHAINING",
                    "sif_id": "TESTLOCK",
                    "installation_number": 1,
                }
            )
            entry = env["verifactu.invoice.entry"].create(
                {
                    "verifactu_chaining_id": chaining.id,
                    "model": "account.move",
                    "document_id": 1,
                    "company_id": env.company.id,
                    "document_hash": "TESTLOCK",
                }
            )
            cls.chaining_id = chaining.id
            cls.entry_id = entry.id

    @classmethod
    def tearDownClass(cls):
        with environment() as env:
            env["verifactu.invoice.entry"].browse(cls.entry_id).unlink()
            env["verifactu.chaining"].browse(cls.chaining_id).unlink()
        super().tearDownClass()

    @mute_logger("odoo.sql_db")
    def test_cron_skips_locked_chaining(self):
        # Patch the send so no real submission happens for any other chaining.
        with patch.object(
            VerifactuInvoiceEntry, "_send_documents_to_verifactu", return_value=None
        ):
            with environment() as env0:
                # env0 holds a row lock on the pending entry.
                env0.cr.execute(
                    "SELECT id FROM verifactu_invoice_entry "
                    "WHERE id = %s FOR UPDATE",
                    (self.entry_id,),
                )
                with environment() as env1:
                    # The cron cannot obtain the lock (55P03). It must skip that
                    # chaining and return normally instead of raising.
                    result = env1[
                        "verifactu.invoice.entry"
                    ]._cron_send_documents_to_verifactu()
                    self.assertTrue(result)
        # The locked entry was skipped, so it stays pending for the next run.
        with environment() as env:
            self.assertEqual(
                env["verifactu.invoice.entry"].browse(self.entry_id).send_state,
                "not_sent",
            )

    @mute_logger("odoo.sql_db")
    def test_cron_skips_serialization_failure(self):
        # A concurrent COMMITTED update on the pending entry makes the cron's
        # SELECT ... FOR UPDATE fail with a serialization error (SQLSTATE 40001)
        # under REPEATABLE READ. The cron must skip that chaining, not abort.
        with patch.object(
            VerifactuInvoiceEntry, "_send_documents_to_verifactu", return_value=None
        ):
            with environment() as env1:
                # Fix env1's snapshot before the concurrent commit happens.
                env1.cr.execute(
                    "SELECT id FROM verifactu_invoice_entry WHERE id = %s",
                    (self.entry_id,),
                )
                env1.cr.fetchall()
                # Another connection updates and COMMITS the same entry.
                with environment() as env0:
                    env0.cr.execute(
                        "UPDATE verifactu_invoice_entry "
                        "SET send_attempt = send_attempt + 1 WHERE id = %s",
                        (self.entry_id,),
                    )
                    env0.cr.commit()
                # env1's FOR UPDATE now raises 40001; the cron must skip and
                # return normally instead of raising.
                result = env1[
                    "verifactu.invoice.entry"
                ]._cron_send_documents_to_verifactu()
                self.assertTrue(result)
        # The conflicted entry was skipped, so it stays pending for the next run.
        with environment() as env:
            self.assertEqual(
                env["verifactu.invoice.entry"].browse(self.entry_id).send_state,
                "not_sent",
            )
