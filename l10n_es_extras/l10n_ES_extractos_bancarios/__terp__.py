{
    "name" : "Importación de extractos bancarios C43",
    "version" : "1.0",
    "author" : "Zikzakmedia SL",
	"description" : """Módulo para la importación de extractos bancarios según la norma C43 de la Asociación Española de la Banca.

Añade un asistente a los extractos bancarios para realizar la importación. El fichero importado queda como fichero adjunto al extracto en cuestión.
Permite definir las cuentas contables por defecto que se asociarán a los conceptos definidos en los fichero de extractos bancarios C43.

La búsqueda de la empresa se hace a partir de:
	1) La referencia2 del registro del extracto que acostumbra a ser la referencia de la operación que da la empresa. Se busca un apunte no conciliado con la misma referencia.
	2) El CIF/NIF que se encuentra en:
	  - Los 9 primeros caracteres de la referencia1 del registro del extracto (Banc Sabadell)
	  - Los caracteres [21:30] de l['conceptos'] (Caja Rural del Jalón)
	3) Búsqueda en los apuntes no conciliados por importe
Si no se encuentra la empresa se asigna la cuenta contable que se haya definido por defecto para el concepto de ese registro.

Elimina el precálculo del importe de la línea del extracto bancario cuando se modifica la empresa (ya que los importes importados ya son los correctos)
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
