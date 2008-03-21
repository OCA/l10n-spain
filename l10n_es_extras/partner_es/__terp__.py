{
    "name" : "Partner ES",
    "version" : "0.2",
    "author" : "Spanish Localization Team",
    "description": """En una instalación por defecto de TinyERP, el formulario de partners consta de 4 pestañas. El campo con el nombre del partner se encuentra en la primera pestaña por lo que si se desea consultar la información de otras pestañas de distintos partners resulta incómodo tener que volver a la primera pestaña para comprobar el nombre de partner. Este módulo resuelve este problema posicionando el nombre y CIF/NIF de las empresas encima de las pestañas, haciendo estos datos accesibles desde cualquier pestaña. Además este módulo:
    * Añade a los partners el campo *Nombre Comercial*
    * Permite validar el CIF/NIF, para ello añade un campo de país a los partners
    * Permite validar las cuentas bancarias, para ello añade un campo de país a los bancos de los partners

Funcionamiento de la validación de la cuenta bancaria:
    * Se descartan todos los caracteres que no sean dígitos del campo número de cuenta.
	* Si los dígitos son 18 calcula los dos dígitos de control
	* Si los dígitos son 20 calcula los dos dígitos de control e ignora los actuales
		Presenta el resultado con el formato "1234 5678 06 1234567890"
	* Si el número de dígitos es diferente de 18 0 20 deja el valor inalterado
    
PENDIENTE
Sería conveniente que la aplicación mostrase un mensaje informativo cuando se introduce un CIF/NIF incorrecto, en lugar de borrarlo directamente sin informar de la acción realizada.
Al igual que sucede con el CIF/NIF, sería conveniente que la aplicación mostrase un mensaje informativo cuando una cuenta bancaria no puede ser validada

	""",
    "depends" : ["base", "base_vat", "base_iban"],
    "init_xml" : [],
    "update_xml" : ['partner_es_view.xml',],
    "active": False,
    "installable": True
}




