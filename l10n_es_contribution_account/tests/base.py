# -*- encoding: utf-8 -*-

# Odoo, Open Source Management Solution
# Copyright (C) 2014-2015  Grupo ESOC <www.grupoesoc.es>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Define bases for the test cases, to avoid redundancy.

Test case logic goes here. Then, in the other modules ``test_*`` in this folder
this logic is merged to test it in all models.
"""

from openerp.tests.common import TransactionCase
from .. import exceptions as ex


class Contact(TransactionCase):
    model = "res.partner"

    def setUp(self, *args, **kwargs):
        super(Contact, self).setUp(*args, **kwargs)
        self.create_record()

    def create_record(self):
        self.record = self.env[self.model].create({"name": str(self)})
        self.is_company = False


class Company(Contact):
    def create_record(self):
        super(Company, self).create_record()
        self.record.is_company = self.is_company = True


class Employee(Contact):
    model = "hr.employee"


class BadInput:
    def test_upper_limit(self):
        "Try to set a code with more than 12 digits."

        code = "1234567890021"

        def write_long_code():
            self.record.contribution_account = code

            # Right now there is no warning or exception when the ORM truncates
            # input, so the only thing I can check here is that it gets
            # truncated. See https://github.com/odoo/odoo/issues/6698
            self.assertEqual(self.record.contribution_account, code[:-1])

        if self.is_company:
            with self.assertRaises(ex.BadLengthCompany):
                write_long_code()
        else:
            write_long_code()

    def test_lower_limit(self):
        "Try to set a code with less than the allowed digits."

        if self.is_company:
            code, exception = "1212345608", ex.BadLengthCompany
        else:
            code, exception = "12123456787", ex.BadLengthPerson

        with self.assertRaises(exception):
            self.record.contribution_account = code

    def test_non_numeric(self):
        "Try to set a non-numeric code."

        with self.assertRaises(ex.NonNumericCode):
            self.record.contribution_account = "bad"


class GoodControlDigit:
    def tearDown(self, *args, **kwargs):
        self.record.contribution_account = self.code
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


class WrongControlDigit:
    def tearDown(self, *args, **kwargs):
        # Ensure the exception is raised
        with self.assertRaises(ex.ControlDigitValidationFailed):
            self.record.contribution_account = self.code

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
