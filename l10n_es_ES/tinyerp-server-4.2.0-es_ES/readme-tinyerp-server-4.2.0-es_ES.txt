===== Traducción servidor TinyERP al español =====

La página del proyecto es:
http://tinyforge.org/projects/es-es/

==== Introducción ====

A partir de la traducción de tinyERP 4.0.3 se ha realizado la traducción completa del sevidor tinyERP 4.2.0 versión estable, unificando los criterios de traducción con una pequeña guía de estilo para mejorar la calidad de la traducción.

La traducción del servidor 4.2.0 ha sido importada/exportada en un servidor versión 4.0.3 para obtener una traducción notablemente mejorada del sevidor 4.0.3 aunque no completa.

==== Instalación ====
Para instalar las traducciones en el servidor, descomprimir el fichero correspondiente en el subdirectorio bin del servidor y ejecutar:

cd <directorio_servidor>/bin
./tinyerp-server.py -d <nombre_base_datos> -l es_ES --i18n-import=tinyerp-server-4.2.0-es_ES.csv

o como administrador a través del cliente de tiny, mediante la opción Administración / Traducciones / Importar idioma.

==== Observaciones ====
El fichero con la traducción ha sido ordenado línea a línea alfabéticamente y eliminadas las líneas repetida con el comando:

  sort -u fichero_entrada.csv > fichero_salida.csv

excepto la primera línea, que tiene que contener:

  type,name,res_id,src,value

Atención: Hay que usar el comando sort con cuidado, pues en la versión 4.2.0 estable contiene algunos textos a traducir multilínea (son textos de ayuda contextual, en el fichero csv empiezan con help). El comando sort disgrega estos textos multilínea en líneas separadas.

Existen un par de errores en la importación de la traducción a partir de un fichero CSV:

* Los textos multilínea no son correctamente importados pues los saltos de línea se pierden al procesar el fichero CSV. Actualmente los textos multilínea traducidos tienen un espacio en blanco al final de cada línea para evitar que los textos de dos líneas diferentes queden juntos. Este bug está reportado en tinyforge.org como [#506] Translation of multi-line text from CSV fails

* Algunos menús que por defecto sólo tiene acceso el usuario admin no son importados correctamente. Son los menús Administración, Configuración, Empleados, etc. Como solución provisional, hay que eliminar todos los registros de la tabla r_ui_menu_group_rel, importar las traducciones y volver a inserir los registros que habían en la tabla ir_ui_menu_group_rel si se desea mantener la restricción de acceso a estos menús. Este bug está reportado en tinyforge.org como [#446] Translation of some menu-items fails.

Equipo traducción tinyERP 4.2.0

Zikzakmedia SL (www.zikzakmedia.com)
Jordi Esteve: jesteve arroba zikzakmedia punto com

y todos los miembros del proyecto http://tinyforge.org/projects/es-es/
