# Roadmap PR `l10n_es_atc_sii_oca`

Alcance del PR ATC: **completar payload, validaciones y libros SII autonómicos**
sin parchear `l10n_es_aeat_sii_oca` salvo acuerdo explícito OCA. Cada ítem enlaza
el test que hoy hace `skipTest` y debe pasar al cerrarse.

Referencias: [FAQ ATC SII](https://www3.gobiernodecanarias.org/tributos/atc/estatico/asistencia_contribuyente/pdf/Preguntas_frecuentes_SII.pdf), listas L8A/L8B, BOC.

## Fuera de este PR (módulos hermanos o upstream)

| Elemento | Motivo | Destino |
|----------|--------|---------|
| Parches genéricos SII peninsular | Política del fork | `l10n_es_aeat_sii_oca` (solo con PR upstream) |
| Impuestos especiales (`ClaveImpuestoEspecial`) | Sin impuestos Odoo equivalentes | Fase 2.7 (follow-up) |
| Error 4100 (`IDVersionSii`) | **Ya resuelto** (1.0 en test) | — |

## Entregado en PR actual (F3 + F4)

| Fase | Entrega | Estado |
|------|---------|--------|
| 3.1–3.5 | Validaciones pre-envío ATC (1295, 1349, 2042, régimen 07, F2 > 3.000 €) | **Hecho** |
| 4.1 | `TipoRectificativa = S` + `ImporteRectificacion` (solo inherit ATC) | **Hecho** |

## Fase 1 — Datos IGIC y mapa (aplazada)

**Motivo:** cubierto por PR v16 en curso; no duplicar en 18.0 hasta alinear ramas.

| # | Entrega | Ficheros | Test a activar |
|---|---------|----------|----------------|
| 1.1 | Añadir `depends`: `l10n_es_igic` | `__manifest__.py` | `test_sale_igic_1_percent_petroleum` |
| 1.2 | Mapa ATC: `igic_r_1` → SFESB | `l10n.es.aeat.map.tax.line.tax.csv`, `atc_sii_map_data.xml` | idem |
| 1.3 | Documentar requisito plan `es_canary_pymes` en tests | `readme/CONFIGURE.md` | `TestL10nEsAtcSiiPayloadBase` |

## Fase 2 — Nodos de payload en facturas (`account.move`) — aplazada

**Motivo:** esperar port a 18.0 del bloque DUA e impuestos de [OCA/l10n-spain#5050](https://github.com/OCA/l10n-spain/pull/5050) (rama 16.0).

**Objetivo:** XML/dict ATC completo en emisión y recepción.

| # | Entrega | Implementación | Test |
|---|---------|----------------|------|
| 2.1 | Régimen **06** → `BaseImponibleACoste` | Campo en línea/ factura o coste en desglose; override `_get_aeat_invoice_dict_out` | `test_sale_regime_06_base_imponible_a_coste` |
| 2.2 | Régimen **14** (obra AAPP) → `FechaOperacion` | Campo `sii_operation_date` (o reutilizar existente); validar NIF P/Q/S/V | `test_sale_regime_14_public_works` |
| 2.3 | **F3** + `FacturasSustituidas` | Tipo factura + relación facturas simplificadas agrupadas | `test_sale_f3_substitution_not_implemented` |
| 2.4 | REPEP compras **15** → `CargaImpositivaImplicita` + `CuotaRecargoMinorista` | Cálculo desde impuesto minorista (`igic_*_cmino`) | `test_purchase_repep_minorista_clave_15` |
| 2.5 | REPEP compras **16** / ventas **18** | Extensión `_get_sii_in_taxes` / dict compra y venta | `test_purchase_repep_pequeño_empresario_clave_16` |
| 2.6 | DUA / importación → `CuotaAIEM` | Integrar con `l10n_es_dua_igic` tras PR #5050 en 18.0 | `test_purchase_dua_aiem_cuota` |
| 2.7 | Impuestos especiales tabaco/combustibles | `ClaveImpuestoEspecial` | follow-up posterior |
| 2.8 | BI ampliado (`N`, deducción diferida) | Campos + payload compra | tests gaps BI |

## Fase 3 — Validaciones pre-envío (negativas locales) — hecho

| # | Entrega | Implementación | Test |
|---|---------|----------------|------|
| 3.1 | F2 con `ImporteTotal` > 3.000 € | `_aeat_check_simplified_limit` | `test_sale_simplified_f2_over_3000_not_allowed` |
| 3.2 | Régimen **07** incompatible con ISP (S2/S3) y exentas E2–E5 | `_aeat_check_regime_07` | `test_sale_regime_07_cash_criterion_isp_incompatible` |
| 3.3 | `BienInversion=S` incompatible con régimen **08** / **18** | `_aeat_check_bien_inversion_regime` | `test_purchase_investment_rejected_regime_08` |
| 3.4 | Coherencia `ImporteTotal` vs bases+cuotas (tolerancia 10 €) | `_aeat_check_importe_total` | `test_importe_total_mismatch_validation` |
| 3.5 | Bloqueo local E2/E3 con régimen **01** (error 1295) | `_aeat_check_regime_01_exempt_export` | `test_sale_export_e2_with_regime_01_payload_documents_atc_rejection` |

## Fase 4 — Rectificativas ATC — hecho

| # | Entrega | Implementación | Test |
|---|---------|----------------|------|
| 4.1 | `TipoRectificativa = S` + `ImporteRectificacion` | `selection_add` en `account.move` ATC | `test_refund_by_substitution_tipo_s_not_supported` |

## Fase 5 — RECC (criterio de caja) — aplazada

**Motivo:** mismo bloque que Fase 2 (DUA / impuestos v18 vía PR #5050).

| # | Entrega | Implementación | Test |
|---|---------|----------------|------|
| 5.1 | Cobros régimen 07 → `SiiFactCOBV1SOAP` | Extensión `account.payment` | `test_recc_cobros_regime_07_not_implemented` |
| 5.2 | Pagos régimen 07 → `SiiFactPAGV1SOAP` | idem | `test_recc_pagos_regime_07_not_implemented` |

## Fase 6 — Libro anual de bienes de inversión — aplazada

**Motivo:** sin equivalente OCA hoy; requiere modelo dedicado.

| # | Entrega | Implementación | Test |
|---|---------|----------------|------|
| 6.1 | Modelo + wizard asiento anual | `models/l10n_es_atc_sii_investment_book.py` | `test_investment_goods_annual_book_0a_not_implemented` |
| 6.2 | Payload: periodo `0A`, prorrata y regularización | `_get_aeat_book_dict` | idem |

## Orden recomendado

```
Fase 3 → Fase 4 (este PR) → Fase 2 + DUA (#5050) → Fase 5 → Fase 1 (igic_r_1) → Fase 6
```

## Criterio de cierre del PR actual

- `invoke test -m l10n_es_atc_sii_oca`: **0 failed, 0 errors**
- Skips permitidos: Fases 1, 2, 5 y 6 (ítems anteriores)

## Estado actual (baseline)

| Área | Cubierto |
|------|----------|
| IGIC 0, 3, 5, 7, 9.5, 15, 20 % ventas S1 | Sí |
| Exentas E1/E2/E3/E5, exportación régimen 02 | Sí |
| No sujetas N1/N2 (art. 9 / localización) | Sí |
| F2 &lt; 3.000 €, bloqueo F2 &gt; 3.000 € | Sí |
| Validaciones 1295, 1349, 2042, régimen 07 | Sí |
| Rectificativa S (sustitución) | Sí |
| ISP, BienInversion compras | Sí |
| Rectificativa I, R1–R4, R5 simplificada, bajas | Sí |
| `IDVersionSii`, mapa ATC, WSDL, SFRBI patch | Sí |
| Payload nodos F2, RECC, libro `0A`, `igic_r_1` | Pendiente |
