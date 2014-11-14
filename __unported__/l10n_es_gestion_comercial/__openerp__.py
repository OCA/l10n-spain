# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2011 Soluntec - Soluciones Tecnológicas (http://www.soluntec.es) All Rights Reserved.
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################
{
    "name": "Gestión Comercial de efectos de facturación",
    "version": "1.0",
    "author": "Soluntec",
    "website": "http://www.soluntec.es",
    "category": "Localisation/Europe",
    "description":
    """
        Este modulo amplia la funcionalidad contable de OpenERP para poder llevar el control de la gestión comercial
        de documentos de cobro/pago y efectos contables.

        Funcionalidades :

        * Se crean diarios de gestión de fectos comerciales, impagos e incobrables.

        * Cuando se realiza un pago de cliente por estos diarios, agrupa los efectos liquidados por ese pago en un nuevo efecto.

        * Este nuevo efecto podrá tener un nuevo vencimiento y tipo de pago definidos en el pago de cliente.

        * Se añaden nuevos campos en la ficha de contabilidad del cliente para poder definir las cuentas a utilizar.. Si están en blanco utilizarán las definidas por defecto en el diario.

        * En la configuración de diarios se añade un check llamado sin efecto contable. Si esta marcado en nuevo efecto lo creará usando la cuenta de cobrables del cliente. De este modo no habrá movimiento alguno de cantidades entre cuenta. Valido para empresas que no quieran usar las cuentas de gestión de efectos.


    """,
    "depends": ["base", "sale", "purchase", "account_voucher"],
    "init_xml": [],
    "demo_xml": [],
    "update_xml": [
        "gestion_comercial_view.xml",
        "account_check_view.xml",
        "gestion_comercial_journals.xml",
        "gestion_comercial_menu.xml",
    ],
    "active": False,
    "installable": False
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
