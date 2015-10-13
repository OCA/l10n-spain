# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2008 Acysos SL. All Rights Reserved.
#                       Ignacio Ibeas <ignacio@acysos.com>
#    Copyright (c) 2008 Pablo Rocandio. All Rights Reserved.
#    AvanzOSC, Advanced Open Source Consulting
#    Copyright (C) 2011-2012 Ainara Galdona (www.avanzosc.com). All Rights Reserved
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
#    $Id$
#
# Refactorización. Acysos S.L. (http://www.acysos.com) 2012
#   Ignacio Ibeas <ignacio@acysos.com>
#
# Migración OpenERP 7.0. Acysos S.L. (http://www.acysos.com) 2013
#   Ignacio Ibeas <ignacio@acysos.com>
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

{
    "name" : "Exportación de ficheros bancarios CSB 19, 32, 34 y 58",
    "version" : "1.6",
    "author" : "Acysos SL, Zikzakmedia SL, Pablo Rocandio, NaN·tic,Odoo Community Association (OCA)",
    "category" : "Localisation/Accounting",
    "description" : """Módulo para la exportación de ficheros bancarios según las normas CSB 19 (recibos domiciliados), CBS 32 (descuento comercial), CSB 58 (anticipos de créditos) y CSB 34 (emisión de transferencias, nóminas, cheques, pagarés y pagos certificados) para poder ser enviados a la entidad bancaria.

Crea un tipo de pago "Recibo domiciliado" con el código RECIBO_CSB. Este código es importante pues permite ejecutar el asistente de creación del fichero de remesas cuando se presiona el botón "Realizar pagos" en la orden de pagos o remesa.

También crea los tipos de pago "Transferencia" (TRANSFERENCIA_CSB), "Pagaré" (PAGARE_CSB), "Cheque" (CHEQUE_CSB), "Pago certificado" (PAGO_CERTIFICADO_CSB).

Antes de generar un fichero bancario CSB habrá que definir un modo de pago que use el tipo de pago anterior y donde se defina la forma de pago (CSB 19, CSB 32, CSB 34 o CSB 58), la compañía que emite el fichero y el sufijo y nombre de compañia a incluir en el fichero.

Al crear el fichero bancario CSB:

  * Se pueden agrupar o no los pagos de una misma empresa y cuenta bancaria
  * El fichero creado se guarda como adjunto de la orden de pagos. Se puede volver a crear el fichero de remesas siempre que sea necesario (puede tener que renombrar el anterior fichero adjunto si tienen el mismo nombre).

También se proporciona un informe para imprimir un listado de los pagos/cobros de la orden de pago/cobro (remesa).

**AVISO:** Si está realizando la instalación de forma local (no desde Aplicaciones), este módulo requiere el módulo *account_payment_extension*, disponible en:

https://launchpad.net/account-payment

""",
    "website" : "www.zikzakmedia.com,www.acysos.com",
    "license" : "AGPL-3",
    "depends" : ["base", "account", "account_payment_extension",],
    "init_xml" : ["remesas_data.xml"],
    "demo_xml" : [],
    "update_xml" : [
                "wizard/export_remesas_view.xml",
                "remesas_report.xml",
                "remesas_view.xml",
                "security/ir.model.access.csv"
                ],
    "installable" : False,
    "active" : False,
}
