Account Banking Sepa - FSDD (Anticipos de crédito)
==================================================

* Este módulo permite establecer el prefijo FSDD en el identificador de un
fichero sepa para el producto nicho de anticipo de crédito, antiguamente
exportado en el cuaderno 58.

Instalación
===========

Para instalar este módulo, es necesario tener disponible el módulo
*account_banking_pain_base* del repositorio
https://github.com/OCA/bank-payment

Uso
===

* Se dispone de un campo "Cobro financiado" en las órdenes de cobro que
al guardarse añade el prefijo FSDD al identificador del la orden de cobro.

Contributors
------------
* Omar Castiñeira Saavedra <omar@comunitea.com>
