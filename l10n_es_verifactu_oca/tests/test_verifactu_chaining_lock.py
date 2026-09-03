# Copyright 2026 FactorLibre - Almudena de La Puente
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from unittest.mock import patch

import psycopg2
from psycopg2 import errorcodes

from odoo.exceptions import UserError

from odoo.addons.l10n_es_verifactu_oca.models.verifactu_mixin import (
    VerifactuChainingLocked,
)

from .common import TestVerifactuCommon


class TestVerifactuChainingLock(TestVerifactuCommon):
    """The chaining row is taken with FOR UPDATE NOWAIT, so a busy chain fails
    instead of queueing. Every caller has to tell that failure apart from a
    permanent one, and the exception type is the only reliable way: the message
    goes through _(), and other UserError come out of the very same call.

    The collision itself is not reproducible here -- the chaining row is created
    inside the test transaction, so no other connection can see it, let alone
    lock it. What is under test is the translation of the error PostgreSQL
    raises into that type.
    """

    def _fail_the_lock(self, pgcode):
        """Make only the chaining SELECT ... FOR UPDATE NOWAIT fail."""
        original = type(self.env.cr).execute

        class _LockError(psycopg2.OperationalError):
            pass

        _LockError.pgcode = pgcode

        def _execute(cr, query, params=None, log_exceptions=None):
            if "FOR UPDATE NOWAIT" in query:
                raise _LockError("injected")
            return original(cr, query, params)

        return patch.object(type(self.env.cr), "execute", _execute)

    def test_a_taken_chaining_row_raises_its_own_error(self):
        self.invoice.action_post()
        self.invoice.last_verifactu_invoice_entry_id = False
        with self._fail_the_lock(errorcodes.LOCK_NOT_AVAILABLE):
            with self.assertRaises(VerifactuChainingLocked) as caught:
                self.invoice._generate_verifactu_chaining()
        self.assertIsInstance(
            caught.exception,
            UserError,
            "Existing callers catch UserError and must keep working",
        )
        # Asserted on the chaining name and not on the wording: the message
        # goes through _() and comes out translated, which is precisely why
        # callers cannot tell this failure apart by its text.
        self.assertIn(self.verifactu_chaining.name, str(caught.exception))

    def test_another_database_error_is_not_disguised_as_a_collision(self):
        """Only 55P03 means contention. Anything else is a different problem
        and must travel as itself, or a permanent failure would be retried for
        ever as if it were transient.
        """
        self.invoice.action_post()
        self.invoice.last_verifactu_invoice_entry_id = False
        with self._fail_the_lock(errorcodes.UNDEFINED_COLUMN):
            with self.assertRaises(psycopg2.OperationalError) as caught:
                self.invoice._generate_verifactu_chaining()
        self.assertNotIsInstance(caught.exception, VerifactuChainingLocked)
