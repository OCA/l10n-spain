Exportación de ficheros bancarios CSB 19, 32, 34 y 58
======================================================

Módulo para la exportación de ficheros bancarios según las normas CSB 19 (recibos domiciliados), CBS 32 (descuento comercial), CSB 58 (anticipos de créditos) y CSB 34 (emisión de transferencias, nóminas, cheques, pagarés y pagos certificados) para poder ser enviados a la entidad bancaria.

Crea un tipo de pago "Recibo domiciliado" con el código RECIBO_CSB. Este código es importante pues permite ejecutar el asistente de creación del fichero de remesas cuando se presiona el botón "Realizar pagos" en la orden de pagos o remesa.

Antes de generar un fichero bancario CSB habrá que definir un modo de pago que use el tipo de pago anterior y donde se defina la forma de pago (CSB 19, CSB 32, CSB 34 o CSB 58), la compañía que emite el fichero y el csb_suffix y nombre de compañia a incluir en el fichero.

Al crear el fichero bancario CSB:

  * Se pueden agrupar o no los pagos de una misma empresa y cuenta bancaria
  * El fichero creado se guarda como adjunto de la orden de pagos. Se puede volver a crear el fichero de remesas siempre que sea necesario (puede tener que renombrar el anterior fichero adjunto si tienen el mismo nombre).

También se proporciona un informe para imprimir un listado de los pagos/cobros de la orden de pago/cobro (remesa).

**AVISO:** Se mantienen los modos de pago CSB19 y CSB 34, porque hay bancos como Ing Direct que no aceptan SEPA.

**AVISO:** Si está realizando la instalación de forma local (no desde Aplicaciones), este módulo requiere el módulo *account_banking_payment_export*, disponible en:

https://github.com/OCA/bank-payment