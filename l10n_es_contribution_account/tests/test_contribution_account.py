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

from openerp.tests.common import TransactionCase
from .. import exceptions as ex


class ContributionAccountCase(TransactionCase):
    def setUp(self, *args, **kwargs):
        super(ContributionAccountCase, self).setUp(*args, **kwargs)

        self.partner = self.env["res.partner"].create({
            "name": "_ContributionAccountCase"})


class BadInputCase(ContributionAccountCase):
    def test_upper_limit(self):
        "Try to set a code with more than 12 digits."

        code = "1234567890021"
        self.partner.is_company = False
        self.partner.contribution_account = code

        # Right now there is no warning or exception when the ORM truncates
        # input, so the only thing I can check here is that it gets truncated.
        # See https://github.com/odoo/odoo/issues/6698
        self.assertEqual(self.partner.contribution_account, code[:-1])

    def test_lower_limit_company(self):
        "Try to set a code with less than 11 digits for a company."

        self.partner.is_company = True
        with self.assertRaises(ex.BadLengthCompany):
            self.partner.contribution_account = "1212345608"

    def test_lower_limit_person(self):
        "Try to set a code with less than 12 digits for a person."

        self.partner.is_company = False
        with self.assertRaises(ex.BadLengthPerson):
            self.partner.contribution_account = "12123456787"

    def test_non_numeric(self):
        "Try to set a non-numeric code."

        with self.assertRaises(ex.NonNumericCode):
            self.partner.contribution_account = "lolailolailo"


class GoodControlDigitCase(ContributionAccountCase):
    def tearDown(self, *args, **kwargs):
        self.partner.contribution_account = self.code
        self.assertEqual(self.partner.contribution_account, self.code)

        super(GoodControlDigitCase, self).tearDown(*args, **kwargs)

    def test_company_1(self):
        self.partner.is_company = True
        self.code = "12023456754"

    def test_company_2(self):
        self.partner.is_company = True
        self.code = "11123456711"

    def test_company_3(self):
        self.partner.is_company = True
        self.code = "03012345656"

    def test_company_4(self):
        self.partner.is_company = True
        self.code = "05123456740"

    def test_company_5(self):
        self.partner.is_company = True
        self.code = "05000789071"

    def test_person_1(self):
        self.partner.is_company = False
        self.code = "120234567863"

    def test_person_2(self):
        self.partner.is_company = False
        self.code = "111234567821"

    def test_person_3(self):
        self.partner.is_company = False
        self.code = "030123456782"

    def test_person_4(self):
        self.partner.is_company = False
        self.code = "051234567820"

    def test_person_5(self):
        self.partner.is_company = False
        self.code = "050007890031"


class WrongControlDigitCase(ContributionAccountCase):
    def tearDown(self, *args, **kwargs):
        # Ensure the exception is raised
        with self.assertRaises(ex.ControlDigitValidationFailed):
            self.partner.contribution_account = self.code

        super(WrongControlDigitCase, self).tearDown(*args, **kwargs)

    def test_company_1(self):
        self.partner.is_company = True
        self.code = "12023456759"

    def test_company_2(self):
        self.partner.is_company = True
        self.code = "11123456719"

    def test_company_3(self):
        self.partner.is_company = True
        self.code = "03012345659"

    def test_company_4(self):
        self.partner.is_company = True
        self.code = "05123456749"

    def test_company_5(self):
        self.partner.is_company = True
        self.code = "05000789079"

    def test_person_1(self):
        self.partner.is_company = False
        self.code = "120234567869"

    def test_person_2(self):
        self.partner.is_company = False
        self.code = "111234567829"

    def test_person_3(self):
        self.partner.is_company = False
        self.code = "030123456789"

    def test_person_4(self):
        self.partner.is_company = False
        self.code = "051234567829"

    def test_person_5(self):
        self.partner.is_company = False
        self.code = "050007890039"
