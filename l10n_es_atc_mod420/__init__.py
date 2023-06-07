# Copyright 2014-2022 Nicolás Ramos (http://binhex.es)
# Copyright 2023 Binhex System Solutions

from . import models


def pre_init_check(cr):
    from odoo.service import common
    from odoo.exceptions import Warning

    version_info = common.exp_version()
    server_serie = version_info.get("server_serie")
    if server_serie != "16.0":
        raise Warning(
            "Este módulo solo es soportado por Odoo Versión 16.0, he encontrado {}.".format(
                server_serie
            )
        )
    from odoo import api, SUPERUSER_ID

    l10n_es_igic = api.Environment(cr, SUPERUSER_ID, {})["ir.module.module"].search(
        [("name", "=", "l10n_es_igic")]
    )
    if not len(l10n_es_igic) or l10n_es_igic.state != "installed":
        raise Warning("Este módulo requiere que esté instalado l10n_es_igic")
    if l10n_es_igic.installed_version != "16.0.4.0.0":
        raise Warning(
            'Este módulo requiere l10n_es_igic en la versión 16.0.4.0.0, encontrada la Version {}. Por favor actualice l10n_es_igic".'.format(
                l10n_es_igic.installed_version
            )
        )
    return True
