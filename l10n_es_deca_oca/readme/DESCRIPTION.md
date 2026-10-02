Este módulo proporciona el documento de control administrativo
electrónico (DeCA) para el transporte terrestre de mercancías, adaptado
a los requisitos legales de España dictados por el Ministerio de
Transportes y Movilidad Sostenible.

El Documento de control electrónico se integra con los albaranes de Odoo
y permite a los transportistas generar, imprimir y compartir el
documento DeCA directamente.

Más información en la página oficial: [Documento Electrónico de Control Administrativo (DeCA)](https://www.transportes.gob.es/transporte-terrestre/profesionales-transporte/servicios-transportista/documento-electronico-control-administrativo-deca).

### Inmutabilidad y Versionado
Para cumplir estrictamente con los requisitos legales sobre el documento DeCA:
* **Generación inmutable**: La primera vez que se imprime o se solicita un documento, se almacena de forma inmutable como archivo adjunto (`v1`).
* **Preservación de URL/QR**: Al compartir el enlace al transportista, siempre servirá de forma dinámica la última versión generada, manteniendo el mismo código QR impreso físicamente.
* **Trazabilidad de Metadatos**: El PDF incluye inyección automática de metadatos (/CreationDate y /ModDate) que indican cuándo se generó la primera versión y cuándo la versión actual, sirviendo como rastro de auditoría.
* **Versionado inteligente**: Si se alteran datos críticos en el albarán (matrículas, transportista, productos o bultos) tras haber emitido un DeCA, el sistema generará automáticamente una nueva versión (`v2`, `v3...`) manteniendo siempre el histórico de archivos PDF previos adjuntos en Odoo.
