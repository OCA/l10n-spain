Presentación de Declaraciones Intrastat
=======================================

Este módulo es una ayuda para presentar las *Declaraciones Intrastat* de la Agencia Tributaria (AEAT). Permite generar un archivo para subir la declaración a la web de la Agencia.

Más información sobre la Declaración Intrastat en la web `AEAT Intrastat <http://www.agenciatributaria.es/AEAT.internet/Inicio/Aduanas_e_Impuestos_Especiales/Intrastat/Intrastat.shtml>`.

Configuración
=============

Para configurar este módulo tienes que:

 * ir al menú Contabilidad > Configuración > Varios > Tipos Intrastat para creaar/verificar los tipos de Intrastat
 * ir al menú Configuración > Compañías > Compañías, editar la compaía actual e ir a la pestaña *Ajustes Intrastat*

Asegurate de que tienes configurado los módulos *intrastat_base* e *intrastat_product* de los cuales este módulo depende

ATENCÓN: hay muchos ajustes para Intrastat y todos ellos han de ser configurados correctamente para generar la declaración con Odoo.

Uso
===

Para generar el archivo de la declaración Intrastat tienes que ir al menú Contabilidad > Informe > Informes legales > Informe Intrastat > Informe AEAT Intrastat y crear una nueva declaración. Dependiendo de tus obligaciones, quizás necesites crear dos declaraciónes: una para exportaciones y otra para importaciones. Para rellenar las líneas de la declaración puede pulsar el botón *Generar líneas desde facturas* y se crearán automáticamente. Tras comprobar que las líneas han sido correctamente generadas, haga click en el botón *Adjuntar fichero AEAT*. Finalmente, conectesé a la `Web de la Agencia Tributaria <https://www.agenciatributaria.gob.es/AEAT.sede/tramitacion/DP01.shtml>` para subir el archivo CSV generado.

Créditos
========

Este módulo se ha creado partiendo del módulo l10n_fr_intrastat_product.

Contribuidores
--------------

* Ismael Calvo <ismael.calvo@factorlibre.com>
* Alexis de Lattre <alexis.delattre@akretion.com>

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose mission is to support the collaborative development of Odoo features and promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
