===== Traducció servidor web eTiny al català =====

La pàgina del projecte és:
http://tinyforge.org/projects/tinyerp-ca/

==== Introducció ====

S'ha realitzat la traducció completa del servidor web eTinyERP 1.0 des de zero a partir de la traducció ja realitzada en castellà. S'ha procurat mantenir el mateix estil i conceptes de la traducció del client GTK 4.2.0.

==== Instal·lació ====
Per instal·lar la traducció en el servidor web copieu els fitxers messages.mo i messages.po a $ETINY/locales/es/LC_MESSAGES

Nota 1: $ETINY és la carpeta a on es troba el servidor web eTiny.

Si es vol tornar a compilar el fitxer messages.mo a partir del fitxer messages.po es pot utilitzar un editor de fitxers po (per exemple el poedit) o bé el programa msgfmt.py inclòs en el client GTK executant:

cd $TERP_CLIENT
python msgfmt.py -o $ETINY/locales/es/LC_MESSAGES/messages.mo  $ETINY/locales/es/LC_MESSAGES/messages.po

Nota 2: $TERP_CLIENT és la carpeta a on es troba el client TinyERP.

==== Observacions ====

Equip de traducció tinyERP 4.2.2, etiny 1.0

Zikzakmedia SL (www.zikzakmedia.com)
Jordi Esteve: jesteve arroba zikzakmedia punt com
Esther Xaus

i tots els membres del projecte http://tinyforge.org/projects/tinyerp-ca/
