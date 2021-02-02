13.0.2.0.0
~~~~~~~~~~

A la hora de integrar con los diferentes sistemas, se utilizará la configuración
definida en `edi`. Es decir, se gestionará con `edi.document` y componentes.

Será potestad de los módulos que utilizen el antiguo `account.invoice.integration`
migrarlo a su configuración respectiva. En la migración no se eliminaran las tablas
antiguas para permitir la migración necesaria.
