# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

"""These are **NOT** tests, just base classes, to avoid redundancy.

These classes test contribution account behavior included in this module, but
this module does not define any real models, just abstract ones, so you are
supposed to inherit these tests in your module to check all is working.

Any instance of any of these classes must have an :attr:`record` attribute that
points to the record being tested. The record can be empty if you want.

See module :mod:`l10n_es_tgss_partner` tests to know how to use this.
"""

from .. import exceptions as ex


class Company(object):
    """Test submodels of :class:`~.contribution_account.CompanyABC`."""
    is_company = True

    def write_code(self, code):
        return self.record.contribution_account_ids.create({
            "owner_id": self.record.id,
            "code": code,
            "owner_model": "res.partner",
        })

    def read_code(self):
        self.env.cache.clear()
        return self.record.contribution_account_ids.code


class Person(object):
    """Test submodels of :class:`~.contribution_account.PersonABC`."""
    is_company = False

    def write_code(self, code):
        self.record.affiliation_number = code

    def read_code(self):
        return self.record.affiliation_number


class BadInput(object):
    def test_upper_limit(self):
        "Try to set a code with more than the allowed digits."
        if self.is_company:
            # Should have 11 digits
            code = "123456789390"
        else:
            # Should have 12 digits
            code = "1234567890023"

        self.write_code(code)

        # Right now there is no warning or exception when the ORM truncates
        # input, so the only thing I can check here is that it gets
        # truncated. See https://github.com/odoo/odoo/issues/6698
        self.assertEqual(self.read_code(), code[:-1])

    def test_lower_limit(self):
        "Try to set a code with less than the allowed digits."

        if self.is_company:
            code, exception = "1212345608", ex.BadLengthError
        else:
            code, exception = "12123456787", ex.BadLengthError

        with self.assertRaises(exception):
            self.write_code(code)

    def test_non_numeric(self):
        "Try to set a non-numeric code."

        with self.assertRaises(ex.NonNumericCodeError):
            self.write_code("bad")


class GoodControlDigit(object):
    def tearDown(self, *args, **kwargs):
        self.write_code(self.code)
        self.assertEqual(self.record.contribution_account, self.code)

        super(GoodControlDigit, self).tearDown(*args, **kwargs)

    def test_1(self):
        self.code = "12023456754" if self.is_company else "120234567863"

    def test_2(self):
        self.code = "11123456711" if self.is_company else "111234567821"

    def test_3(self):
        self.code = "03012345656" if self.is_company else "030123456782"

    def test_4(self):
        self.code = "05123456740" if self.is_company else "051234567820"

    def test_5(self):
        self.code = "05000789071" if self.is_company else "050007890031"


class WrongControlDigit(object):
    def tearDown(self, *args, **kwargs):
        # Ensure the exception is raised
        with self.assertRaises(ex.ControlDigitValidationError):
            self.write_code(self.code)

        super(WrongControlDigit, self).tearDown(*args, **kwargs)

    def test_1(self):
        self.code = "12023456759" if self.is_company else "120234567869"

    def test_2(self):
        self.code = "11123456719" if self.is_company else "111234567829"

    def test_3(self):
        self.code = "03012345659" if self.is_company else "030123456789"

    def test_4(self):
        self.code = "05123456749" if self.is_company else "051234567829"

    def test_5(self):
        self.code = "05000789079" if self.is_company else "050007890039"
