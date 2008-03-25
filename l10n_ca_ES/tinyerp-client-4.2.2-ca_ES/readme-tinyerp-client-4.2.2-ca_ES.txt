===== Traducció client TinyERP al català =====

La pàgina del projecte és:
http://tinyforge.org/projects/tinyerp-ca/

==== Introducció ====

A partir de la traducció de tinyERP 4.0.3 s'ha realitzat la traducció completa del client tinyERP 4.2.2 versió estable.

==== Instal·lació ====
Per instal·lar la traducció en el client copiar el fitxer es.po en $TERP_CLIENT/bin/po/es.po i executar:

cd $TERP_CLIENT
python msgfmt.py -o bin/share/locale/es/LC_MESSAGES/tinyerp-client.mo bin/po/es.po

Nota 1: $TERP_CLIENT és la carpeta on es troba el client TinyERP.
Nota 2: Si no es vol compilar el fitxer es.po també es proporciona el fitxer tinyerp-client.mo. El fitxer tinyerp-client.mo cal deixar-lo a la carpeta $TERP_CLIENT/bin/share/locale/es/LC_MESSAGES

==== Observacions ====
Alguns texts no estan traduïts en el client perquè no apareixen en els fitxers .po originals. Aquest bug està reportat en tinyforge.org com [#505] Translations are not up-to-date

Si hi hagués problemes amb la codificació, prova això:
iconv -f ISO_8859-14 -t utf8 es.po > es.utf8.po


Equip traducció tinyERP 4.2.2

Zikzakmedia SL (www.zikzakmedia.com)
Jordi Esteve: jesteve arroba zikzakmedia punt com
Esther Xaus

i tots els membres del projecte http://tinyforge.org/projects/tinyerp-ca/
