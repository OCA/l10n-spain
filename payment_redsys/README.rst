Pasarela de pago Redsys
=======================

Este módulo añade la opción de pago a través de la pasarela de Redsys.


Parámetros
----------

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

* **URL_OK/URL_KO**: Durante el proceso del pago, y una vez que
  se muestra al cliente la pantalla con el resultado del mismo, es
  posible redirigir su navegador a una URL para las transacciones
  autorizadas y a otra si la transacción ha sido denegada. A éstas
  se las denomina URL_OK y URL_KO, respectivamente. Se trata
  de dos URLs que pueden ser proporcionadas por el comercio.

Nota
----

Se tiene que verificar la configuración del comercio en el
módulo de administración de Redsys, donde la opción “Parámetros en las
URLs” debe tener el valor “SI”.
