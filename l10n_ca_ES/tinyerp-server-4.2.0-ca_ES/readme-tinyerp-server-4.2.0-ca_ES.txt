===== Traducció servidor TinyERP al català =====

La pàgina del projecte és:
http://tinyforge.org/projects/tinyerp-ca/

==== Introducció ====

A partir de la traducció de tinyERP 4.0.3 s'ha realitzat la traducció completa del sevidor tinyERP 4.2.0 versió estable al castellà, unificant els criteris de traducció amb una petita guia d'estil per millorar la qualitat de la traducció. A partir de la traducció al castellà que s'ha anat corregint durant un període de 3 mesos s'ha realitzat la traducció al català.

==== Instal·lació ====
Per instal·lar les traduccions al servidor, descomprimir el fitxer corresponent en el subdirectori bin del servidor i executar:

cd < directori_servidor>/bin
./tinyerp-server.py -d <nom_base_dades> -l ca_ES --i18n-import=tinyerp-server-4.2.0-ca_ES.csv

o com a administrador a través del client de tiny, mitjançant l'opció Administració / Traduccions / Importa idioma.

==== Observacions ====
El fitxer amb la traducció ha estat ordenat línia a línia alfabèticament i eliminades les línies repetida amb la comanda:

sort -o fitxer_entrada.csv > fitxer_sortida.csv

excepte la primera línia, que ha de contenir:

type,name,res_id,src,value

Atenció: Cal usar la comanda sort amb compte, doncs en la versió 4.2.0 estable conté alguns texts a traduir multilínia (són texts d'ajuda contextual, en el fitxer csv comencen amb help). La comanda sort disgrega aquests texts multilínia en línies separades.

Existeixen un parell d'errors en la importació de la traducció a partir d'un fitxer CSV:

* Els texts multilínia no són correctament importats ja que els salts de línia es perden en processar el fitxer CSV. Actualment els texts multilínia traduïts tenen un espai en blanc al final de cada línia per evitar que els texts de dues línies diferents quedin junts. Aquest bug està reportat en tinyforge.org com [#506] Translation of multiline text from CSV fails

* Alguns menús que per defecte només té accés l'usuari admin no són importats correctament. Són els menús Administració, Configuració, Empleats, etc. Com solució provisional, cal eliminar tots els registres de la taula r_ui_menu_group_rel, importar les traduccions i tornar a inserir-se els registres que havien a la taula ir_ui_menu_group_rel si es desitja mantenir la restricció d'accés a aquests menús (cosa totalment recomanable). Aquest bug està reportat en tinyforge.org com [#446] Translation of some menu-items fails.


Equip traducció tinyERP 4.2.0

Zikzakmedia SL (www.zikzakmedia.com)
Jordi Esteve: jesteve arroba zikzakmedia punt com
Esther Xaus

i tots els membres del projecte http://tinyforge.org/projects/tinyerp-ca/

