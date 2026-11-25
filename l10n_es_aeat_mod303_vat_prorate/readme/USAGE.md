1.  Realizar la declaración 303 de la forma habitual.
2.  El IVA deducible ya vendrá minorado por el porcentaje de la
    prorrata.
3.  En la casilla 44, se mostrará el importe de la prorrata que se
    minoró.

- Nota: En la versión 18, el cálculo definitivo de la prorrata se realiza directamente desde el formulario del mod303.report.  El botón “Calcular prorrata definitiva” solo se mostrará si with_vat_prorate está activado y period_type es '4T' o '12'. En versiones anteriores (v14), este cálculo se realizaba a través de un wizard independiente.

- El cálculo de la prorrata definitiva (art. 104 LIVA) elige los
  impuestos de venta por el tipo y la causa de exención que Odoo core
  asigna a cada impuesto español:

  - Numerador (operaciones con derecho a deducción, art. 94.Uno LIVA):
    impuestos de tipo sujeto, sujeto ISP o agricultura, sea cual sea el
    porcentaje (también 0 % y 7,5 %), exentos por los arts. 21 a 25
    (causas E2 a E5: exportaciones, entregas intracomunitarias...) y no
    sujetos por reglas de localización.
  - Denominador: lo anterior más los exentos por el art. 20 (E1) y por
    otras causas (E6).
  - No cuentan en ningún término los no sujetos por el art. 7
    (art. 104.Tres.5.º) ni los impuestos que Odoo core deja fuera de la
    declaración (por ejemplo, los genéricos de la ventanilla única).
