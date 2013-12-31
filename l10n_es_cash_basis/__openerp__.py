# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c):
#        2013       Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                   Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
#
#    This program is free software: you can redistribute it and/or modify it
#    under the terms of the GNU Affero General Public License as published by
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
    "name" : "Criterio de caja para España",
    "version" : "0.2",
    "author" : "Spanish Localization Team",
    "contributors": [
        'Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>'
    ],
    'website' : 'https://launchpad.net/openerp-spain',
    "category" : "Accounting/Localization",
    "description": """
Implementación del Régimen Especial del Criterio de Caja (RECC) español
=======================================================================

La implementación sólo contempla el plan contable para PYMEs (de hecho, las
empresas que utilicen el plan contable completo no pueden acogerse a este
régimen especial, ya que su facturación es mayor de 2 M de euros).

Define los impuestos, códigos de impuestos y las cuentas necesarias para
manejar por separado el IVA pendiente de cobrar y de pagar. Para ello, utiliza
el módulo *account_chart_update*, que se encuentra disponible en la rama 6.1 de
este proyecto de Launchpad:

https://launchpad.net/account-financial-tools

El asistente de actualización se ejecuta automáticamente cuando se instala el
módulo. En la plantilla del plan contable, hay que elegir 'Plantilla PGCE
PYMES 2008', y poner el nº de dígitos que se utiliza para el plan de cuentas.
El resto de opciones puede quedarse tal cual. Si se tiene más de una compañía,
habrá que ejecutar manualmente este asistente para cada compañía.

Para que sea efectivo, el usuario debe colocar a los proveedores que se hayan
acogido a este régimen la posición fiscal 'Régimen Especial de Criterio de
Caja (RECC)' en su ficha.

Si la compañía usuaria de OpenERP se va a acoger al criterio de caja, habrá
que establecer por defecto para todos los clientes que la posición fiscal sea
la anteriormente dicha. *AVISO*: Si esta norma se incumple, el sistema creará
asientos incorrectos que pueden derivar en la ilegalidad.

El módulo también modifica el comportamiento del voucher para que al realizar
el pago, se lleven los saldos contables a sus cuentas correspondientes,
constando ya en los informes de impuestos en los apartados adecuados para su
presentación a Hacienda (NO ESTÁ IMPLEMENTADO AÚN).

*ADVERTENCIA*: Este módulo no gestiona la condición de que el IVA se debe
repercutir o soportar forzosamente, aunque no se haya cobrado/pagado, el día
31 del año inmediatamente posterior a la fecha de factura, por lo que esas
operaciones habrá que hacerlas a mano y, en caso de que después se haga el
cobro/pago, eliminar la parte del movimiento de saldos entre las cuentas de IVA
pendiente a las cuentas de IVA definitivas (ya que se encontrarán hechas
previamente).
""",
    "license" : "AGPL-3",
    "depends" : [
        "l10n_es",
        "account_chart_update",
    ],
    "data" : [
        'account_account_pymes.xml',
        'tax_codes_pymes.xml',
        'taxes_pymes.xml',
        'fiscal_templates_pymes.xml',
        'l10n_es_cash_basis_data.xml',
    ],
    "installable": True,
}
