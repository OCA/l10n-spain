# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) All Rights Reserved
#        2004-2011:  Pexego Sistemas Informáticos. (http://pexego.es)
#        2012:       NaN·Tic  (http://www.nan-tic.com)
#        2013:       Acysos (http://www.acysos.com)
#                    Joaquín Pedrosa Gutierrez (http://gutierrezweb.es)
#        2014:       Serv. Tecnol. Avanzados - Pedro M. Baeza
#                    (http://www.serviciosbaeza.com)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
{
    'name': "AEAT Model 347",
    'version': "1.1",
    'author': "Spanish Localization Team,Odoo Community Association (OCA)",
    'website': "https://github.com/OCA/l10n-spain",
    'contributors': [
        'Pexego (http://www.pexego.es)',
        'ASR-OSS (http://www.asr-oss.com)',
        'NaN·tic (http://www.nan-tic.com)',
        'Acysos (http://www.acysos.com)',
        'Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>',
        'Joaquín Gutierrez (http://gutierrezweb.es)',
    ],
    'category': "Localisation/Accounting",
    'description': """
Presentación del Modelo AEAT 347
================================

(Declaración Anual de Operaciones con Terceros)
Basado en la Orden EHA/3012/2008, de 20 de Octubre, por el que se aprueban los diseños físicos y lógicos del 347.

De acuerdo con la normativa de la Hacienda Española, están obligados a presentar el modelo 347:
-----------------------------------------------------------------------------------------------
* Todas aquellas personas físicas o jurídicas que no esten acogidas al regimen
  de módulos en el IRPF, de naturaleza pública o privada que desarrollen
  actividades empresariales o profesionales, siempre y cuando hayan realizado
  operaciones que, en su conjunto, respecto de otra persona o Entidad,
  cualquiera que sea su naturaleza o carácter, hayan superado la cifra de
  3.005,06 € durante el año natural al que se refiere la declaración. Para el
  cálculo de la cifra de 3.005,06 € se computan de forma separada las entregas
  de biene y servicios y las adquisiciones de los mismos.
* En el caso de Sociedades Irregulares, Sociedades Civiles y Comunidad de Bienes
  no acogidas el regimen de módulos en el IRPF, deben incluir las facturas sin
  incluir la cuantía del IRPF.
* En el caso de facturas de proveedor con IRPF, no deben ser presentadas en este
  modelo. Se presentan en el modelo 190. Desactivar en la ficha del proveedor
  la opción de "Incluir en el informe 347".

De acuerdo con la normativa no están obligados a presentar el modelo 347:
-------------------------------------------------------------------------
* Quienes realicen en España actividades empresariales o profesionales sin
  tener en territorio español la sede de su actividad, un establecimiento
  permanente o su domicilio fiscal.
* Las personas físicas y entidades en régimen de atribución de rentas en
  el IRPF, por las actividades que tributen en dicho impuesto por el
  régimen de estimación objetiva y, simultáneamente, en el IVA por los
  régimenes especiales simplificados o de la agricultura, ganadería
  y pesca o recargo de equivalencia, salvo las operaciones que estén
  excluidas de la aplicación de los expresados regímenes.
* Los obligados tributarios que no hayan realizado operaciones que en su
  conjunto superen la cifra de 3.005,06 €.
* Los obligados tributarios que hayan realizado exclusivamente operaciones
  no declarables.
* Los obligados tributarios que deban informar sobre las operaciones
  incluidas en los libros registro de IVA (modelo 340) salvo que realicen
  operaciones que expresamente deban incluirse en el modelo 347.

(http://www.boe.es/boe/dias/2008/10/23/pdfs/A42154-42190.pdf)

**AVISO:** Este módulo requiere el módulo *account_invoice_currency*,
disponible en:

https://launchpad.net/account-financial-tools
    """,
    'license': "AGPL-3",
    'depends': [
        "base_vat",
        "l10n_es_aeat",
        "account_invoice_currency",
    ],
    'data': [
         "account_period_view.xml",
         "res_partner_view.xml",
         "wizard/export_mod347_to_boe.xml",
         "report/mod347_report.xml",
         "security/ir.model.access.csv",
         "security/mod_347_security.xml",
         "mod347_view.xml",
    ],
    'installable': True,
    'active': False,
    'images': [
        'images/l10n_es_aeat_mod347.png',
    ],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
