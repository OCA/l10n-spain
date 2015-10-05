# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .base import Company
from openerp.addons.l10n_es_tgss.tests import contribution_account


class BadInputCase(Company,
                   contribution_account.BadInput):
    pass


class GoodControlDigitCase(Company,
                           contribution_account.GoodControlDigit):
    pass


class WrongControlDigitCase(Company,
                            contribution_account.WrongControlDigit):
    pass
