# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

"""These are **NOT** tests, just base classes, to avoid redundancy.

These classes test disability percentage behavior included in this module, but
this module does not define any real models, just abstract ones, so you are
supposed to inherit these tests in your module to check all is working.

Any instance of any of these classes must have an :attr:`record` attribute that
points to the record being tested. The record can be empty if you want.

See module :mod:`l10n_es_tgss_partner` tests to know how to use this.
"""

from .. import exceptions as ex


class DisabilityPercentageCase:
    def test_good(self):
        self.record.disability_percentage = 0
        self.record.disability_percentage = 33
        self.record.disability_percentage = 100

    def test_less_than_0(self):
        with self.assertRaises(ex.OutOfRangeError):
            self.record.disability_percentage = -1

    def test_more_than_100(self):
        with self.assertRaises(ex.OutOfRangeError):
            self.record.disability_percentage = 101
