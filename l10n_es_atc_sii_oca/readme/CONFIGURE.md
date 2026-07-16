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

**Causas de exención IGIC (E1–E8):** el módulo añade las 8 causas de exención
del IGIC canario, con los literales actualizados según la normativa vigente:

- **E1:** Capítulo I del Decreto Legislativo 1/2025
- **E2:** Artículo 11 de la Ley 20/1991 (exportaciones)
- **E3:** Artículo 12 de la Ley 20/1991 (asimiladas a exportaciones)
- **E4:** Artículo 13 de la Ley 20/1991 (zonas francas y depósitos)
- **E5:** Artículo 25 de la Ley 19/1994, del IGIC (bienes de inversión REF)
- **E6:** Artículo 47 de la Ley 19/1994 (ZEC)
- **E7:** Artículo 90 del Decreto Legislativo 1/2025 (REPEP)
- **E8:** Exenta Otros / Ley 20/1991

Configure la causa en el producto o en la posición fiscal; el módulo no altera
automáticamente la clave de régimen ni la causa de exención.

**Art. 25 REF — Bienes de inversión (Lista L32):** para operaciones con clave de
régimen **17** (compras) o **19** (ventas), el módulo exige el bloque
`DatosArticulo25` en el payload SII. Configure:

1. En el producto o en la posición fiscal, seleccione la causa de exención **E5**
   y el **Tipo de bien Art. 25 (L32)** correspondiente.
2. En la factura, en la pestaña SII, rellene los campos del grupo **Art. 25 REF**:
   - **Pago anticipado** (S/N)
   - **Tipo de documento** (notarial, privado u otros)
   - Si es notarial, **Nº de protocolo** y **Nombre del notario** (obligatorios)

El módulo bloquea localmente los envíos sin estos datos (errores ATC 2028/2031).

**Validaciones pre-envío (F3):** la ATC rechaza el envío
(error 1295) si se informa la clave de régimen **01** (régimen general) junto con
`CausaExencion` **E2** o **E3** (exportaciones y asimiladas). Esas causas exigen
la clave **02** (exportación). El módulo **bloquea localmente** esa combinación al
validar o enviar la factura (`UserError` con referencia al error 1295).
