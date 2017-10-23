Utilidad para generar el archivo de municipios desde GeoNames
=============================================================

Debido a que Correos España no permite disponer de manera abierta y gratuita 
de la base de datos de códigos postales (sólo se pueden realizar consultas 
puntuales desde su web), han surgido diversas iniciativas para recolectar 
dicha información. 

Por eso, se utiliza una fuente alternativa que es el servicio GeoNames, que 
permite descargar un archivo con toda esa información desde
http://download.geonames.org/export/zip/ES.zip.

Desgraciadamente, ninguna de las fuentes (incluida la de correos que se 
consulta desde la web) tiene las tildes en los nombres, por lo que los nombres 
de municipios no son completamente correctos.

Esta utilidad transforma los datos obtenidos en un archivo XML llamado
'l10n_es_toponyms_zipcodes.xml', necesario para el funcionamiento del módulo 
l10n_es_toponyms.

Uso del script
==============

1. Para ejecutar el script, es necesario tener la librería requests
2. Ejecuta el script poniendo: `python gen_toponyms_geonames.py`
3. Esperar hasta que el shell indique "Proceso terminado".
4. Copiar el archivo `l10n_es_toponyms_zipcodes.xml` generado a la carpeta 
   `wizard` del módulo, sobreescribiendo el anterior.

Créditos
========
Script realizado por Pedro M. Baeza, inspirado en el código del módulo:
https://github.com/OCA/partner-contact/tree/8.0/base_location_geonames_import
