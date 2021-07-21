Parámetros
~~~~~~~~~~

* **Nombre del comercio**: Indicaremos el nombre del comercio.

* **Número de comercio (FUC)**: Indicaremos el número de comercio que
  nuestra entidad nos ha comunicado.

* **Clave secreta de encriptación**: Indicaremos la clave de encriptación
  que tiene el comercio.

* **Número de terminal**: Indicaremos el terminal del TPV.

* **Tipo de firma**: Seleccionaremos el tipo de firma del comercio.

* **Tipo de moneda**: Seleccionaremos la moneda de nuestro terminal TPV
  (Normalmente EUR - Euros).

* **Tipo de transacción**: Indicaremos el tipo de transacción, 0.

* **Idioma TPV**: Indicaremos el idioma en el TPV.

* **Método de pago**: Indicaremos qué tipo de pago se debe aceptar, pago con
  tarjeta, Bizum u otro de los disponibles.

* **Porcentaje de pago**: Indicar el porcentaje de pago que se permite, si
  se deja a 0.0 se entiende 100%.

Nota
~~~~

Se tiene que verificar la configuración del comercio en el
módulo de administración de Redsys, donde la opción “Parámetros en las
URLs” debe tener el valor “SI”.

En caso de que exista más de una base de datos en la instalación, cuando la
pasarela de pago envía el formulario a "/payment/redsys/return" odoo no sabe
con que base de datos procesar esta información, por lo que hay que establecer
los parametros **dbfilter** y **dbname** en el archivo de configuración.

Para mostrar simultáneamente en el comercio electrónico varios de los métodos
de pago que proporciona Redsys, como pago con tarjeta y Bizum por ejemplo,
debemos duplicar el medio de pago y escoger en el campo método de pago el que
corresponda en cada caso.

En el caso de Bizum, el titular del TPV deberá solicitar al banco su activación.
