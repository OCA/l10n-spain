# Roadmap `l10n_es_atc_sii_oca`

Pendiente respecto al código actual. Lo ya cubierto está en la descripción del
módulo y en los tests que no hacen `skipTest`.

Referencias: [FAQ ATC SII](https://www3.gobiernodecanarias.org/tributos/atc/estatico/asistencia_contribuyente/pdf/Preguntas_frecuentes_SII.pdf),
listas L8A/L8B, BOC.

## Fuera de este módulo

| Elemento | Motivo |
|----------|--------|
| Parches del SII peninsular | Van en `l10n_es_aeat_sii_oca` |
| Plantillas `igic_sop_1_inv` e `igic_sop_i_1_inv` | No existen en el plan canario de 18.0; no se referencian |
| Grupos de impuesto 9,5 / 15 / 20 | Viven en el plan contable, no en este addon |
| Módulo DUA IGIC de 16.0 (`l10n_es_dua_igic`) | No está portado a 18.0 |

## Pendiente

| # | Entrega | Notas | Test |
|---|---------|--------|------|
| 1 | Régimen **14** (AAPP): inyectar `FechaOperacion` desde `sii_operation_date` y validar NIF P/Q/S/V (error 1292) | El campo existe en la factura; el XML no lo escribe | `test_sale_regime_14_public_works` |
| 2 | Régimen **06**: `BaseImponibleACoste` | No hay nodo en el payload | `test_sale_regime_06_base_imponible_a_coste` |
| 3 | **F3** y `FacturasSustituidas` | Tipo de factura de sustitución de simplificadas agrupadas | `test_sale_f3_substitution_not_implemented` |
| 4 | REPEP **16** y **18** completos | La compra exenta (`igic_p_ex`) con clave 16 ya va solo con `BaseImponible`. Falta el resto del régimen | `test_purchase_repep_pequeño_empresario_clave_16` cubre solo la exenta |
| 5 | `CuotaRecargoMinorista` | La clave entra en el total del desglose si el nodo existe; no se genera desde un impuesto | — |
| 6 | DUA: `CuotaAIEM` | El mapa DUA marca `sii_dua_invoice`, mete el IGIC de importación en el desglose y quita `InversionSujetoPasivo` en F5/LC (1339/1340). Falta la cuota AIEM | `test_purchase_dua_aiem_cuota` |
| 7 | Art. 25: bloqueo local 2028 / 2031 / 2036 | Se inyecta `DatosArticulo25` si hay tipo de bien (L32). No hay `UserError` si faltan documento, protocolo o notario | — |
| 8 | RECC régimen 07: cobros y pagos | `SiiFactCOBV1SOAP` / `SiiFactPAGV1SOAP` | `test_recc_cobros_regime_07_not_implemented`, `test_recc_pagos_regime_07_not_implemented` |
| 9 | Libro anual de bienes de inversión (periodo `0A`) | Modelo, wizard, prorrata y regularización | `test_investment_goods_annual_book_0a_not_implemented` |
| 10 | Impuestos especiales | `ClaveImpuestoEspecial` (tabaco, combustibles). Sin impuestos equivalentes en Odoo | — |

## Cerrado (no reabrir)

- `IDVersionSii` siempre `1.0` (test y producción). La ATC rechaza `1.1` con el error 4100.
- Mapa ATC de los tipos nuevos del plan: `igic_r_1`, `igic_sop_1`, `igic_sop_1_s`, `igic_ISP1`, `igic_p_re01`, compras `*_cmino`, `*_retail`, `*_retail_inv` y DUA `igic_sop_i_*`.
- Compra minorista (clave 15): `CargaImpositivaImplicita` con tipo nominal y `CuotaDeducible` igual a la CII (1330 / 1350).
- Compra `*_retail`: cuota no deducible (1329 en clave 17).
- Venta minorista (clave 17): solo exenta; si no hay causa, `igic_cmino` usa **E1**. Claves 02 / 17 / 18 / 19 sin sujeta no exenta (1281).
