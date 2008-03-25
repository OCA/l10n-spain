===== Traducción servidor web eTiny al español =====

La página del proyecto es:
http://tinyforge.org/projects/es-es/

==== Introducción ====

Se ha realizado la traducción completa del servidor web eTinyERP 1.0 desde cero. Se ha procurado mantener el mismo estilo y conceptos de la traducción del cliente GTK 4.2.0.

==== Instalación ====
Para instalar la traducción en el servidor web copiar los ficheros messages.mo y messages.po en $ETINY/locales/es/LC_MESSAGES

Nota 1: $ETINY es la carpeta donde se encuentra el servidor web eTiny.

Si se quiere volver a compilar el fichero messages.mo a partir del fichero messages.po se puede utilizar editores de ficheros po (por ejemplo el poedit) o bien el programa msgfmt.py incluido en el cliente GTK. Ejecutar:

cd $TERP_CLIENT
python msgfmt.py -o $ETINY/locales/es/LC_MESSAGES/messages.mo  $ETINY/locales/es/LC_MESSAGES/messages.po

Nota 2: $TERP_CLIENT es la carpeta donde se encuentra el cliente TinyERP.

==== Observaciones ====

Equipo traducción tinyERP 4.2.0, etiny 1.0

Zikzakmedia SL (www.zikzakmedia.com)
Jordi Esteve: jesteve arroba zikzakmedia punto com

y todos los miembros del proyecto http://tinyforge.org/projects/es-es/
