Pasarela de pago Redsys
=======================

Este módulo añade la opción de pago a través de la pasarela de Redsys.


Parámetros
----------

* **Merchant URL**: http://[dominioweb]/payment/redsys/return

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

* **Porcentaje de pago**: Indicar el porcentaje de pago que se permite, si
se deja a 0.0 se entiende 100%

Nota
----

Se tiene que verificar la configuración del comercio en el
módulo de administración de Redsys, donde la opción “Parámetros en las
URLs” debe tener el valor “SI”.

En caso de que exista más de una base de datos en la instalación, cuando la
pasarela de pago envía el formulario a "/payment/redsys/return" odoo no sabe
con que base de datos procesar esta información.
Por lo que hay que establecer los parametros **dbfilter** y **dbname** en
**openerp-server.conf**.

Instalación
-----------

Para utilizar este módulo, necesita la biblioteca `pycrypto
<https://pypi.python.org/pypi/pycrypto>`_ instalada en su sistema::

    pip install pycrypto
