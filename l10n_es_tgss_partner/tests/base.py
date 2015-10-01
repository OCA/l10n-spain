# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tests.common import TransactionCase


class Contact(TransactionCase):
    """Base class for testing behavior in contact partners."""
    is_company = False

    def setUp(self, *args, **kwargs):
        super(Contact, self).setUp(*args, **kwargs)
        self.create_record()

    def create_record(self):
        self.record = self.env["res.partner"].create(
            {"name": str(self),
             "is_company": self.is_company})


class Company(Contact):
    """Base class for testing behavior in company partners."""
    is_company = True
