# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008-2010 Zikzakmedia S.L. (http://zikzakmedia.com)
#                            Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2012-2013, Grupo OPENTIA (<http://opentia.com>)
#                            Dpto. Consultoría <consultoria@opentia.es>
#    Copyright (c) 2013-2015 Serv. Tecnol. Av. (http://www.serviciosbaeza.com)
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
#    Copyright (c) 2015 FactorLibre (www.factorlibre.com)
#                       Carlos Liébana <carlos.liebana@factorlibre.com>
#                       Hugo Santos <hugo.santos@factorlibre.com>
#    Copyright (c) 2015 GAFIC consultores (www.gafic.com)
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
    "name": "Spanish Charts of Accounts (PGCE 2008)",
    "version": "5.1",
    "author": "Spanish Localization Team,"
              # "Zikzakmedia S.L.,"
              # "Grupo Opentia,"
              # "Serv. Tecnol. Avanzados - Pedro M. Baeza,"
              # "FactorLibre,"
              # "GAFIC consultores,"
              "Odoo Community Association (OCA)",
    "website": 'https://github.com/OCA/l10n-spain',
    "category": "Localization/Account Charts",
    "description": """
Plan contable e impuestos de España (PGCE 2008)
===============================================

* Define las siguientes plantillas de cuentas:
  * Plan general de cuentas español 2008.
  * Plan general de cuentas español 2008 para pequeñas y medianas empresas.
  * Plan general de cuentas español 2008 para asociaciones.
* Define plantillas de impuestos para compra y venta.
* Define plantillas de códigos de impuestos.
* Define posiciones fiscales para la legislación fiscal española.

**IMPORTANTE:** Ésta es una versión mejorada con respecto al módulo que se
encuentra en la versión estándar de Odoo, por lo que es conveniente instalar
ésta para disponer de los últimos datos actualizados.

Si en la base de datos a aplicar ya se encuentra instalado el plan contable de
la compañía, será necesario actualizarlo con el módulo *account_chart_update*,
disponible en https://github.com/OCA/account-financial-tools. **AVISO:**
Después de actualizar, será necesario cambiar el impuesto de venta por
defecto en la pestaña Configuración > Contabilidad, y además sustituir en los
productos el mismo por "x% IVA (servicios)" o "x% IVA (bienes)" según
corresponda en cada caso. Se puede utilizar para ello el módulo *mass_editing*
del repositorio https://github.com/OCA/server-tools.

Por último, si se procede del l10n_es v3.0, serán necesarios ajustes manuales
al actualizar el plan de cuentas, como crear a mano la cuenta 472000.

Historial
---------

* v5.1: Renombrado todo lo relacionado con arrendamientos para no incluir la
  palabra "IRPF", ya que no es como tal IRPF.
* v5.0: Se ha rehecho toda la parte de impuestos para dar mayor facilidad de
  consulta de los datos para las declaraciones de la AEAT y para cubrir todas
  las casuísticas fiscales españolas actuales. Éstas son las características
  más destacadas:

  * Desdoblamiento de los impuestos principales para bienes y para servicios.
  * Nuevo árbol de códigos de impuestos orientado a cada modelo de la AEAT.
  * Nuevos códigos para los códigos de impuestos para facilitar su
    actualización.
  * La casilla del modelo viene ahora en la descripción, no en el código.
  * Posiciones fiscales ajustadas para el desdoblamiento.
  * Nuevo impuesto y posición fiscal para retención IRPF 19%.
  * Nuevo impuesto para revendedores con recargo de equivalencia.
  * Nuevas posiciones fiscales para retenciones de arrendamientos.
  * Pequeños ajustes en cuentas contables.
* v4.1: Cambio en el método que obtiene el nombre del impuesto e intercambiados
  los campos descripción/nombre para que no aparezca los códigos en documentos
  impresos ni en pantalla.
* v4.0: Refactorización completa de los planes de cuentas, con las siguientes
  caracteristicas:

  * Creacion de un plan común a los tres planes existentes, que reúne las
    cuentas repetidas entre ellos.
  * Eliminación de la triplicidad de impuestos y de códigos de impuestos.
  * Asignación de códigos a los impuestos para facilitar su actualización.
  * Eliminación de duplicidad de tipos de cuentas.
    """,
    "license": "AGPL-3",
    "depends": ["account", "base_vat", "base_iban"],
    "data": [
        "data/account_type.xml",
        "data/account_chart_template.xml",
        "data/account_account_common.xml",
        "data/account_account_full.xml",
        "data/account_account_pymes.xml",
        "data/account_account_assoc.xml",
        "data/tax_codes_common.xml",
        "data/taxes_common.xml",
        "data/fiscal_positions_common.xml",
        "data/account_chart_template_post.xml",
        "data/l10n_es_wizard.xml",
    ],
    "installable": True,
    'images': ['images/config_chart_l10n_es.png', 'images/l10n_es_chart.png'],
}
