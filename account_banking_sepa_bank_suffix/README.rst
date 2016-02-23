Account Banking Sepa - Sufijos variables por modo de pago y FSDD
================================================================

* Este módulo permite cambiar el sufijo de los identificadores sepa a través
del modo de pago.
* Este módulo permite establecer el prefijo FSDD en el identificador de un
fichero sepa para el producto nicho de anticipo de crédito, antiguamente
exportado en el cuaderno 58.

Instalación
===========

Para instalar este módulo, es necesario tener disponible el módulo
*account_banking_pain_base* del repositorio
https://github.com/OCA/bank-payment

Configuración
=============

* Se dispone de un campo sufijo en el modo de pago que si está establecido
substituye al configurado en la compañía
* Se dispone de un campo "Cobro financiado" en las ordenes de cobro que
al guardarse añade el prefijo FSDD al nombre del la orden de cobro.

Contributors
------------
* Omar Castiñeira Saavedra <omar@comunitea.com>
