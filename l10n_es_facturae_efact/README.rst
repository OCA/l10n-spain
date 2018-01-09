.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=================================================================
Envío de la facturación electrónica española (Factura-E) a e.Fact
=================================================================

Este módulo permite la gestión del envío de la facturación electrónica española
a el servicio de envío de facturas de Catalunya (e.Fact).

La gestión del envío se realiza mediante un canal SSH.

Instalación
===========

Este módulo depende del módulo *l10n_es_facturae* y sus dependencias

Configuración
=============

* Configurar los parámetros de envío de e.Fact a cada empresa y partners necesarios
* Se debe configurar el servidor, puerto, usuario y password de envío
* Por defecto se añaden los campos de configuración de produccion
* El certificado debe estar en los known_hosts

Uso
===

* Accedemos a un cliente y le configuramos la factura electrónica
* Accedemos a una factura validada del cliente y pulsamos el botón
  'Enviar a FACe'
* Podremos añadir adjuntos que al envío de la factura original
* Pulsamos 'Enviar' en el registro de envío a FACe
* Si el envío es correcto, nos mostrará el resultado y el número de registro
* Si el envío es correcto, podremos actualizar el estado de forma online
* Si el envío es correcto, podremos solicitar la anulación de la factura
  pulsando 'Cancelar Envío' e introduciendo el motivo
* Un registro Enviado correctamente no puede ser Eliminado
* Sólo puede existir un envío Enviado correctamente
* Se genera una tarea programada que actualiza los registros enviados
  correctamente no pagados y no anulados

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/189/11.0

Credits
=======

Contributors
------------

* Enric Tobella <etobella@creublanca.es>

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
