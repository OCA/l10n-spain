# -*- encoding: utf-8 -*-
{
    "name" : "Adaptación de partner para Estado Español",
    "version" : "1.0",
    "author" : "Spanish Localization Team",
    "description": """Funcionalidades:
    * Añade el campo *Nombre Comercial* a las empresas
    * Añades campos nombre largo, CIF y web a los bancos
    * Añade datos de 191 bancos y cajas españolas extraídos del registro oficial del Banco de España
    * Permite validar las cuentas bancarias, para ello añade un campo de país a los bancos de las empresas

Funcionamiento de la validación de la cuenta bancaria:
    * Se descartan todos los caracteres que no sean dígitos del campo número de cuenta.
    * Si los dígitos son 18 calcula los dos dígitos de control
    * Si los dígitos son 20 calcula los dos dígitos de control e ignora los actuales
        Presenta el resultado con el formato "1234 5678 06 1234567890"
    * Si el número de dígitos es diferente de 18 0 20 deja el valor inalterado
NOTA
Se ha eliminado la validación de CIF/NIF españoles, pues el módulo base_vat de OpenERP 5.0 añade un campo CIF/NIF en la pestaña de contabilidad de las empresas y la validación automática de los CIF de 27 paises europeos. Los CIFs deben introducirse añadiendo al principio los 2 caracteres que identifican cada país en mayúsculas (ES para España), por ejemplo ESB64425879

NOTA: Éste módulo añade un asistente en Empresas/Configuración/Bancos para la importación de todos los bancos y cajas de España. Antes de ejecutar éste asistente deberá tener importadas las provincias disponibles en el módulo l10n_ES_toponyms.
""",
    "depends" : [
        "base",
        "base_iban",
        "l10n_ES_toponyms",
        ],
    "init_xml" : [],
    "update_xml" : [
        "partner_es_view.xml",
        ],
    "active": False,
    "installable": True
}




