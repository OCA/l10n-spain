===== Traducción cliente TinyERP al español =====

La página del proyecto es:
http://tinyforge.org/projects/es-es/

==== Introducción ====

A partir de la traducción de tinyERP 4.0.3 se ha realizado la traducción completa del cliente tinyERP 4.2.2 versión estable.

==== Instalación ====
Para instalar la traducción en el cliente copiar el fichero es.po en $TERP_CLIENT/bin/po/es.po y ejecutar:

cd $TERP_CLIENT
python msgfmt.py -o bin/share/locale/es/LC_MESSAGES/tinyerp-client.mo bin/po/es.po 

Nota 1: $TERP_CLIENT es la carpeta donde se encuentra el cliente TinyERP.
Nota 2: Si no se quiere compilar el fichero es.po también se proporciona el fichero tinyerp-client.mo. El fichero tinyerp-client.mo hay que dejarlo en la carpeta $TERP_CLIENT/bin/share/locale/es/LC_MESSAGES

==== Observaciones ====
Algunos textos no estan traducidos en el cliente porque no aparecen en los ficheros .po originales. Este bug está reportado en tinyforge.org como [#505] Translations are not up-to-date

Si hubiera problemas con la codificación, prueba esto:
iconv -f ISO_8859-14 -t utf8 es.po >  es.utf8.po


Equipo traducción tinyERP 4.2.2

Zikzakmedia SL (www.zikzakmedia.com)
Jordi Esteve: jesteve arroba zikzakmedia punto com

y todos los miembros del proyecto http://tinyforge.org/projects/es-es/
