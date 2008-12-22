# -*- encoding: utf-8 -*-
{
    "name" : "Remesas de recibos CSB 19 y CSB 58",
    "version" : "1.5",
    "author" : "Acysos SL, Zikzakmedia SL, Pablo Rocandio",
    "description" : """Módulo para la exportación de remesas de recibos según las normas CSB 19 (recibos domiciliados) y CSB 58 (anticipos de créditos) para poder ser enviados a la entidad bancaria.

Crea un tipo de pago "Recibo domiciliado" con el código RECIBO_CSB. Este código es importante pues permite ejecutar el asistente de creación del fichero de remesas cuando se presiona el botón "Realizar pagos" en la orden de pagos o remesa.

Antes de generar un fichero de remesas habrá que definir un modo de pago que use el tipo de pago anterior y donde se defina la forma de pago (CSB 19 o CSB 58), la compañía que emite el fichero y el sufijo y nombre de compañia a incluir en el fichero (lo que en la versión 4.2 se definía como la cuenta de remesas).

Al crear el fichero de remesa:

  * Se pueden agrupar o no los pagos de una misma empresa y cuenta bancaria
  * El fichero creado se guarda como adjunto de la orden de pagos. Se puede volver a crear el fichero de remesas siempre que sea necesario (puede tener que renombrar el anterior fichero adjunto si tienen el mismo nombre).

También se proporciona un informe para imprimir un listado de los recibos de la remesa.
""",
    "website" : "www.zikzakmedia.com",
    "license" : "GPL-2",
    "depends" : ["base", "account", "account_payment_extension",],
    "init_xml" : ["remesas_data.xml"],
    "demo_xml" : [],
    "update_xml" : ["remesas_report.xml", "remesas_view.xml", "remesas_wizard.xml",],
    "installable" : True,
    "active" : False,
}
