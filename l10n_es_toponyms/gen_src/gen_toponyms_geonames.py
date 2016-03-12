# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
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
import os.path
import requests
import tempfile
import StringIO
import unicodecsv
import zipfile


def filter_city(originalName):
    """
    Pone correctamente la capitalización de palabras como 'De', 'Las', 'Los',
    cuando son palabras intermedias en el nombre de la ciudad.
    """
    return originalName.replace(' De ', ' de ').replace(' Del ', ' del ').\
        replace(' La ', ' la ').replace(' Las ', ' las ').\
        replace(' El ', ' el ').replace(' Los ', ' los ')


if __name__ == "__main__":
    url = "http://download.geonames.org/export/zip/ES.zip"
    print 'Comenzando descarga de %s' % url
    res_request = requests.get(url)
    if res_request.status_code != requests.codes.ok:
        print 'Error descargando archivo: %s.' % res_request.status_code
        exit(res_request.status_code)
    f_geonames = zipfile.ZipFile(StringIO.StringIO(res_request.content))
    tempdir = tempfile.mkdtemp(prefix='openerp')
    f_geonames.extract('ES.txt', tempdir)
    print 'Archivo descomprimido'
    data_file = open(os.path.join(tempdir, 'ES.txt'), 'r')
    data_file.seek(0)
    print 'Generando XML...'
    output = open("l10n_es_toponyms_zipcodes.xml", 'w')
    output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    output.write('<openerp>\n')
    output.write(' ' * 4 + '<data noupdate="1">\n')
    cont = 0
    for row in unicodecsv.reader(
            data_file, encoding='utf-8', delimiter='	'):
        cont += 1
        output.write(' ' * 8 +
                     '<record id="city_ES_%s" model="res.better.zip">\n' %
                     cont)
        output.write(' ' * 12 + '<field name="state_id" ref="'
                                'l10n_es_toponyms.ES%s"/>\n' % row[1][:2])
        output.write(' ' * 12 + '<field name="city">%s</field>\n' %
                     filter_city(row[2]).encode('utf-8'))
        output.write(' ' * 12 + '<field name="name">%s</field>\n' % row[1])
        output.write(' ' * 12 + '<field name="country_id" ref="base.es"/>\n')
        output.write(' ' * 8 + '</record>\n')
    data_file.close()
    output.write(' ' * 4 + '</data>\n')
    output.write('</openerp>\n')
    # Cerrar archivo
    output.close()
    print "Proceso terminado"
