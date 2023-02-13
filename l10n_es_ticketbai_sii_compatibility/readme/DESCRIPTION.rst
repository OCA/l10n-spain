Este módulo evita el envío de facturas emitidas al Suministro Inmediato de
Información (SII) en caso de que TicketBAI se encuentre activado.

Las facturas emitidas que no se envían al SII son marcadas como exentas de
envío.

Sin este módulo hacienda rechaza los envíos de las facturas al SII con los
errores con códigos 9121, 9122 y 9123: *El NIF emisor no puede proceder al
registro de la operación a través del SII, dado que se encuentra obligado a
remitir dicha información por el Servicio TicketBAI y, en su caso, a
complementarla por el Servicio Osatu*.

`Documentación hacienda Gipuzkoa <https://www.gipuzkoa.eus/documents/2456431/3114636/02-SII_11_Gipuzkoa_CAS_Documento+de+validaciones+y+errores_Fase+5/0c96dcf1-abda-1334-3fbb-a1a2b0af8181>`_
