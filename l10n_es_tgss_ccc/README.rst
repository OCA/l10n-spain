.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Cuenta de cotización de la TGSS
===============================

Las empresas en España necesitan tener un CCC_ (Código de Cuenta de Cotización)
para diversas actividades y comunicaciones relacionadas con la Tesorería
General de la Seguridad Social (TGSS).

Los trabajadores en España también necesitan su NAF_ (Número de Afiliación, o
Número de la Seguridad Social) para los mismos fines.

Este módulo añade ese campo a las fichas de los contactos.

Además, se ejecuta la validación con el dígito de control para asegurarse de
que el código introducido es el correcto.

Instalación
===========

Para instalar este módulo, necesita:

* Instalar el repositorio `l10n-spain`_.

Uso
===

Para usar este módulo, necesita:

* Crear o editar un contacto.

* Introducir código en el campo *Cuenta de cotización* que ahora verá en el
  formulario.

Tenga en cuenta que:

* Si el contacto es una empresa, el CCC debe tener 11 dígitos.

* Si el contacto es una persona física, el NAF debe tener 12 dígitos.

* En cualquier caso, debe introducirse sin guiones, espacios ni separadores de
  ningún tipo. **Únicamente debe introducir dígitos.**

* Si recibe un mensaje de error que indica que el dígito de control es
  incorrecto, lo más probable es que haya introducido un número erróneo.

Para más información, por favor visite:

* https://www.odoo.com/forum/help-1

* https://github.com/OCA/l10n-spain

Problemas conocidos / Hoja de ruta
==================================

* Si se establece un código de cuenta de cotización de más de 12 dígitos, los
  que excedan serán recortados sin previo aviso. `Incidencia relacionada
  <https://github.com/odoo/odoo/issues/6698>`_.

Credits
=======

Contributors
------------

* Jairo Llopis <j.llopis@grupoesoc.es>

Agradecimientos especiales para la web usuariosred.es, por publicar la
explicación del `algoritmo necesario para comprobar los dígitos de control
<http://usuariosred.es/el-digito-de-control-en-los-numeros-de-afiliacion>`_.

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.


.. _CCC: http://www.seg-social.es/Internet_1/Empresarios/Inscripcion/InscEmpresar2k9/InscEmpCCC2k9/index.htm
.. _l10n-spain: https://github.com/OCA/l10n-spain
.. _NAF: http://www.seg-social.es/Internet_1/Normativa/095179?ssSourceNodeId=1139&C1=1001&C2=2004#A21
