# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2011 NaN Projectes de Programari Lliure, S.L.
#                    http://www.NaN-tic.com
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
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

{
    "name": "Secuencia para facturas separada de la secuencia de asientos",
    "version": "1.1",
    "author": "Localización española de OpenERP",
    "website": "https://launchpad.net/openerp-spain",
    "category": "Accounting",
    "license": "AGPL-3",
    "description": """
Este módulo separa los números de las facturas de los de los asientos. Para
ello, convierte el campo number de 'related' a campo de texto normal, y le
asigna un valor según una nueva secuencia definida en el diario
correspondiente.

Su uso es obligatorio para España, ya que legalmente las facturas deben llevar
una numeración única y continua, lo que no es compatible con el sistema que
utiliza OpenERP por defecto.

**AVISO**: Hay que configurar las secuencias correspondientes para todos los
diarios de ventas, compras, abono de ventas y abono de compras utilizados
después de instalar este módulo.
""",
    "depends": [
        'account',
    ],
    "data": [
        'account_view.xml',
    ],
    "demo": [],
    "active": False,
    "installable": True,
}
