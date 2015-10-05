# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .base import Contact
from openerp.addons.l10n_es_tgss.tests import contribution_account


class BadInputCase(Contact,
                   contribution_account.BadInput):
    pass


class GoodControlDigitCase(Contact,
                           contribution_account.GoodControlDigit):
    pass


class WrongControlDigitCase(Contact,
                            contribution_account.WrongControlDigit):
    pass
