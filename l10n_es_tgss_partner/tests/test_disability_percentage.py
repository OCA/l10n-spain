# -*- coding: utf-8 -*-
# © 2015 Grupo ESOC Ingeniería de servicios, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .base import Contact
from openerp.addons.l10n_es_tgss_base.tests import disability_percentage


class DisabilityPercentageCase(Contact,
                               disability_percentage.DisabilityPercentageCase):
    pass
