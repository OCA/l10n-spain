# -*- encoding: utf-8 -*-
{
    "name" : "Recibos y remesas de recibos CSB 19 y CSB 58",
    "version" : "1.5",
    "author" : "Acysos SL, Zikzakmedia SL, Pablo Rocandio",
    "description" : """Módulo para la gestión de:
  * Gestión de remesas de recibos y su posterior exportación según las normas CSB 19 (recibos domiciliados)
    y CSB 58 (anticipos de créditos) para poder ser enviados a la entidad bancaria.

Puede funcionar con o sin el módulo partner_es que comprueba los 2 dígitos de control de la C.C.

Modificaciones de Zikzakmedia SL:
Corregida y mejorada para instalación TinyERP estándar 4.2.0
Botón para generar los archivos y guardarlos en el disco duro

Modificaciones de Pablo Rocandio:
Añadidas las cuentas de remesas. Con parte del código del módulo de remesas se 
crea un módulo de tipos de pago (account_paytype) que se añade como dependencia 
de remesas. Se modifica también el código para poder modificar el número de 
cuenta y fecha de vencimiento a nivel de recibo.
""",
    "website" : "www.acysos.com",
    "license" : "GPL-2",
    "depends" : ["base","account","account_payment_extension",],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : ['remesas_report.xml','remesas_view.xml','remesas_wizard.xml',],
    "installable" : True,
    "active" : False,
}
