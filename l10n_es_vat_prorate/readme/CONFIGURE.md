Para configurar la prorrata general:

- Acceda al menú Facturación > Configuración > AEAT > Actualizar Prorrata de IVA.
  También puede acceder directamente desde la compañía
- Marque que aplica prorrata.
- Defina el porcentaje de prorrata (se aplica por fechas).

Los impuestos de las facturas de proveedor se dividirán según la
prorrata activa. Se prorratean los impuestos de compra de IVA deducible
según el tipo de impuesto que Odoo core asigna a cada impuesto español
(sujeto, sujeto ISP, agricultura y DUA). No se prorratea el IGIC
(impuestos con aplicabilidad IGIC), porque el modelo 303 solo declara
IVA. Se puede cambiar en cada impuesto con el campo "Con prorrata de
IVA". La marca se vuelve a calcular si se cambia el tipo de impuesto, su
aplicabilidad, su uso o si la compañía activa o desactiva la prorrata,
pero no al editar otros datos del impuesto.

Si una línea de factura tiene un porcentaje de deducibilidad menor del
100 % (columna "Profesional" de Odoo core, por ejemplo el combustible de
un vehículo afectado al 50 %, art. 95 LIVA), Odoo core lleva la parte no
deducible de la cuota a la parte privada y la prorrata se aplica sobre la
cuota que queda deducible (art. 104.Uno LIVA).


Para configurar la prorrata especial:

- Acceda al menú Facturación > Configuración > AEAT > Actualizar Prorrata de IVA.
  También puede acceder directamente desde la compañía
- Marque que aplica prorrata de IVA especial.
- Marque el valor por defecto de la prorrata especial.

En las líneas de factura aparecerá un nuevo campo editable, con el valor por defecto configurado,
que permitirá definir que líneas serán prorrateadas.
