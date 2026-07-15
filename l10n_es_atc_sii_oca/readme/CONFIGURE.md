Después de instalar el módulo, vaya a **Contabilidad → Configuración → Ajustes** y,
para cada compañía que opere bajo IGIC, establezca el campo **Agencia Tributaria** como
**Agencia Tributaria Canaria (1.0)** (registro definido por `l10n_es_aeat`).

El módulo seleccionará automáticamente el mapa de impuestos **SII - ATC** para cualquier
compañía cuya agencia tributaria sea la ATC. No se requiere configuración manual
adicional del mapa.

**Versión del protocolo SII (`IDVersionSii`):** en la cabecera del XML enviado a la ATC
el módulo usa **1.1 en producción** (versión vigente del protocolo) y **1.0 cuando está
activo el modo de prueba SII**, porque el entorno de cautela de la ATC solo admite 1.0.
Esto es independiente del nombre mostrado de la agencia en la configuración de la compañía.

Para utilizar el entorno de pruebas, habilite la casilla **Modo de prueba
SII** en los ajustes de la compañía. Todos los envíos se redirigirán entonces a los
puntos de conexión de ``middlewarecaut``.

En producción se usan los endpoints de ``sede.gobiernodecanarias.org`` definidos en
los datos del módulo (sin sufijo ``?wsdl``). Al conectar con zeep, el módulo añade
``?wsdl`` solo en la URL de descarga del WSDL; las llamadas SOAP usan el endpoint
sin ese sufijo.

**Causas de exención y clave de régimen (ATC):** la ATC rechaza el envío
(error 1295) si se informa la clave de régimen **01** (régimen general) junto con
``CausaExencion`` **E2** o **E3** (exportaciones y asimiladas). Esas causas exigen
la clave **02** (exportación). El módulo **bloquea localmente** esa combinación al
validar o enviar la factura (``UserError`` con referencia al error 1295), además de
documentar la regla aquí. Para servicios exentos interiores (p. ej. sanitarios
o educativos), use la causa **E1** (Art. 50 Ley 4/2012), compatible con el
régimen 01. Configure la causa en el producto o en la posición fiscal; el módulo
no altera automáticamente la clave de régimen ni la causa de exención.
