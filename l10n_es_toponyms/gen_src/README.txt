##############################################################################
#
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

Utilidades para generar el archivo de municipios desde varias fuentes de datos
==============================================================================

Debido a que Correos España no permite disponer de manera abierta y gratuita 
de la base de datos de códigos postales (sólo se pueden realizar consultas 
puntuales desde su web), han surgido diversas iniciativas para recolectar 
dicha información. 

Hay dos BDs comunitarias principales:

- La que se puede descargar de www.codigospostales.com. Algo más desfasada, pero
  directamente con un archivo.

- La fuente de datos de GeoNames, que se accede con web services, que devuelven
  archivos XML para cada consulta de un código postal. Parece estar más 
  actualizada. Un posible ejemplo de consulta sería:
  http://ws.geonames.org/postalCodeSearch?postalcode=13250&country=ES.

Desgraciadamente, ninguna de las BDs (incluida la de correos que se consulta 
desde la web) tiene las tildes en los nombres, por lo que los nombres de 
ciudades no son completamente correctos.

USO DEL SCRIPT PARA GEONAMES
==============================================================================
Esta utilidad consulta al webservice de GeoNames por cada uno de los posibles
códigos postales entre 1000 y 53000, volcando los resultados en el archivo 
'l10n_es_toponyms_zipcodes.xml', necesario para el funcionamiento del módulo 
l10n_es_toponyms. Al ser un gran número de consultas web, el proceso puede 
tardar bastante, y el propio servidor establece un límite máximo de consultas 
(en el momento de escribir esto, el límite era de 2000 por hora). Por eso, 
hay que ejecutar varias veces el script poniendo un parámetro para empezar 
desde ese punto. 

1. Cuando se ejecuta por primera vez, se pone:
		python gen_toponyms_geonames.py
2. El script se parará en un momento dado, indicando el CP hasta donde ha
   llegado. Habrá que esperar el tiempo indicado.
3. Volver a ejecutar el script, con el parámetro --start y el número de CP
   donde se ha quedado:
		python gen_toponyms_geonames.py --start número
4. Repetir el paso 3 tantas veces como sea necesario hasta que el script
   indique "Proceso terminado".
5. Copiar el archivo 'l10n_es_toponyms_zipcodes.xml' generado a la carpeta 
   'wizard' del módulo, sobreescribiendo el anterior.

USO DEL SCRIPT PARA WWW.CODIGOSPOSTALES.COM
==============================================================================
Esta utilidad convierte el archivo descargado de www.codigospostales.com
en el archivo l10n_es_toponyms_zipcodes.xml, necesario para el funcionamiento 
del módulo l10n_es_toponyms.

1. Descargar archivo de www.codigospostales.com
2. Descomprimir el archivo .zip en una carpeta.
3. Ejecutar:
		python gen_toponyms_www_codigospostales_com.py <ruta_de_la_carpeta_descomprimida>
4. Copiar el archivo 'l10n_es_toponyms_zipcodes.xml' generado a la carpeta 
   'wizard' del módulo, sobreescribiendo el anterior.
