# -*- encoding: utf-8 -*-
{
	"name" : "Instal·lación PYME estándar (1er paso)",
	"version" : "1.0",
	"author" : "Zikzakmedia SL",
	"category" : "Generic Modules/Others",
	"website": "http://www.zikzakmedia.com",
	"description": """Instal·lación OpenERP para una PYME estándar (1er paso).

Instala los módulos habituales de una PYME del Estado Español: ventas, compras, TPV, productos, stocks, contabilidad y facturación, pagos, remesas de recibos, plan contable 2008, topónimos.

Cuando se ejecute el asistente de configuración de contabilidad (account) deberá omitir el paso, pués la selección del plan contable y la creación de ejercicios y períodos fiscales lo realiza este módulo y l10_ES_pyme_custom de forma automática.

Después de instalar este módulo y todas sus dependencias, deberá crear los topónimos del Estado Español (crear las provincias mediante el asistente que se ejecuta automáticamente) y las cuentas contables a partir de la plantilla (mediante el menú Gestión financiera/Configuración/Contabilidad financiera/Plantillas/Generar plan contable a partir de una plantilla de plan contable).

Posteriormente, instalando el módulo l10_ES_pyme_custom, se instalaran los módulos restantes: l10n_ES_extractos_bancarios, l10n_ES_partner""",
	"depends" : ["base", "account", "account_payment", "account_payment_extension", "point_of_sale", "product", "sale", "sale_payment", "purchase", "stock", "label", "partner_spam", "l10n_ES_remesas", "l10n_chart_ES", "l10n_ES_toponyms", "l10n_ES_partner_data", "l10n_ES_partner_seq"],
	"init_xml" : [],
	"demo_xml" : [],
	"update_xml" : [],
	"active": False,
	"installable": True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: