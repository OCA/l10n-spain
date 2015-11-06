# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tests.common import TransactionCase
from openerp.addons.l10n_es_tgss.tests import contribution_account


class Contact(contribution_account.Person, TransactionCase):
    """Base class for testing behavior in contact partners."""
    def setUp(self, *args, **kwargs):
        super(Contact, self).setUp(*args, **kwargs)
        self.record = self.env["res.partner"].create(
            {"name": str(self),
             "is_company": self.is_company})


class Company(contribution_account.Company, Contact):
    """Base class for testing behavior in company partners."""
