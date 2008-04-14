{
    "name" : "Recibos y remesas de recibos CSB 19 y CSB 58",
    "version" : "1.0",
    "author" : "ACYSOS S.L.",
	"description" : """Módulo para la gestión de recibos (permite marcarlos como cheque/pagaré recibido), 
gestión de remesas de recibos y su posterior exportación en norma CSB 19 y CSB 58
para poder ser enviados a la entidad bancaria.
Puede funcionar con o sin el módulo partner_es que comprueba los 2 dígitos 
de control de la C.C.
Corregida y mejorada para instalación TinyERP estándar 4.2.0: ZIKZAKMEDIA S.L.
Cuentas de remesas añadidas por Pablo Rocandio
""",
	"website" : "www.acysos.com",
	"license" : "GPL-2",
    "depends" : ["base","account"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : ['recibos_view.xml','remesas_report.xml','remesas_sequence.xml','remesas_view.xml','remesas_workflow.xml',],
    "installable" : True,
    "active" : False,
}
