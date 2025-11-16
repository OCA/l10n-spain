> - Refactorización SII-VERI\*FACTU en l10nes_aeat de los métodos que
>   sean comunes.
> - Envío separado de la confirmación de la factura
>   (cron.trigger/queque.job)
> - Control de errores del sistema, generar avisos. (caída de aeat,
>   errores de conexión, etc.)
> - Posibilidad de consultar el estado de las facturas enviadas.
> - Operaciones exentas y causas de exención.
> - Crear un selection con todos los valores posibles de codigos de
>   error, para poder guardarlo y agrupar las facturas por ese código.
> - Contemplar el tiempo de espera entre envíos de registros cuando AEAT
>   devuelve un tiempo superior a 60 segundos.

CASOS NO CUBIERTOS: 1 - Modificación de facturas enviadas (AEAT
recomienda generar rectificativa). Según AEAT: Si los errores detectados
tras la emisión NO están contemplados en el ROF, pero afectan a campos
del registro de facturación (RF) generado al emitir la factura (que,
digamos, “no se ven” en la factura impresa, es decir, son campos
“internos”, como ciertas codificaciones tributarias), se debe corregir
la factura original (esos datos “internos” de la misma) y se debe
generar un RF de alta de subsanación de esa factura donde conste ya la
nueva información que proceda. Estos casos deberían ser MUY POCO
FRECUENTES. 2 - Anulación de facturas enviadas (AEAT recomienda generar
rectificativa). Según AEAT: "Si se considera que "toda la factura" en sí
misma está mal o no debería haberse emitido, siempre que para
solucionarlo no deba emplearse algún procedimiento (de rectificativa u
otro) previsto en el ROF, se podrá "anular" generando para ello un RF de
anulación. Estos casos deberían ser MUY POCO FRECUENTES."
