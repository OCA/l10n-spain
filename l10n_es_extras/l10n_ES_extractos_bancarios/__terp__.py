{
    "name" : "Importación de extractos bancarios C43",
    "version" : "1.0",
    "author" : "Zikzakmedia SL",
	"description" : """Módulo para la importación de extractos bancarios según la norma C43 de la Asociación Española de la Banca.

Añade un asistente a los extractos bancarios para realizar la importación.
Permite definir las cuentas contables por defecto que se asociarán a los conceptos definidos en los fichero de extractos bancarios C43.

La búsqueda del partner se hace a partir de:
	* La referencia2 del registor del extracto que acostumbra a ser la referencia de la operación que da el partner
	* El CIF/NIF que se encuentra en los 9 primeros caracteres de la referencia1 del registro del extracto (¿Esto es válido para los extractos bancarios de todas las entidades? Comprobado para Banc Sabadell)	
""",
	"website" : "www.zikzakmedia.com",
	"license" : "GPL-2",
    "depends" : ["base","account","partner_es","l10n_sp_2008",],
    "init_xml" : ['extractos_conceptos.xml',],
    "demo_xml" : [],
    "update_xml" : ['extractos_view.xml','extractos_wizard.xml',],
    "installable" : True,
    "active" : False,
}
