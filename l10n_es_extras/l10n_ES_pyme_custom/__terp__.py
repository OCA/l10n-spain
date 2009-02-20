# -*- encoding: utf-8 -*-
{
    "name" : "Instal·lación PYME estándar (2o paso)",
    "version" : "1.0",
    "author" : "Zikzakmedia SL",
    "category" : "Generic Modules/Others",
    "website": "http://www.zikzakmedia.com",
    "description": """Instal·lación OpenERP para una PYME estándar (2o paso).

Instala los módulos de importación de extractos bancarios y datos de bancos españoles y su validación.

Previamente debe instalar el módulo l10_ES_pyme_install y crear los topónimos del Estado Español (crear las provincias mediante el asistente que se ejecuta automáticamente) y las cuentas contables a partir de la plantilla (mediante el menú Gestión financiera/Configuración/Contabilidad financiera/Plantillas/Generar plan contable a partir de una plantilla de plan contable.)""",
    "depends" : ["l10n_ES_pyme_install", "l10n_ES_partner", "l10n_ES_extractos_bancarios"],
    "init_xml" : ["pyme_data.xml"],
    "demo_xml" : [],
    "update_xml" : [
        "pos_view.xml",
    ],
    "active": False,
    "installable": True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: