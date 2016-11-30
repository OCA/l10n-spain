# -*- coding: utf-8 -*-
# Copyright 2013-2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import os.path
import requests
import tempfile
import StringIO
import unicodecsv
import zipfile


def filter_city(originalName):
    """Pone correctamente la capitalización de palabras como 'De', 'Las',
    'Los', cuando son palabras intermedias en el nombre de la ciudad.
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
    output.write('<odoo noupdate="1">\n')
    cont = 0
    reader = unicodecsv.reader(data_file, encoding='utf-8', delimiter='	')
    for row in reader:
        cont += 1
        output.write(' ' * 8 +
                     '<record id="city_ES_%s" model="res.better.zip">\n' %
                     cont)
        state = row[6].lower()
        if state == 'me':
            state = 'ml'  # FIXME: While Odoo changes this
        output.write(
            ' ' * 12 +
            '<field name="state_id" ref="base.state_es_{}"/>\n'.format(state)
        )
        output.write(' ' * 12 + '<field name="city">%s</field>\n' %
                     filter_city(row[2]).encode('utf-8'))
        output.write(' ' * 12 + '<field name="name">%s</field>\n' % row[1])
        output.write(' ' * 12 + '<field name="country_id" ref="base.es"/>\n')
        output.write(' ' * 8 + '</record>\n')
    data_file.close()
    output.write('</odoo>\n')
    output.close()
    print "Proceso terminado"
