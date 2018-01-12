# -*- coding: utf-8 -*-
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.modules.registry import RegistryManager
from openerp.addons.l10n_es_aeat_mod349.hooks import post_init_hook


def migrate(cr, version):
    if not version:
        return
    registry = RegistryManager.get(cr.dbname)
    post_init_hook(cr, registry)
