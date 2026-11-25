# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from xml.sax.saxutils import escape

import requests

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, tagged
from odoo.tools import mute_logger

from ..models.transaher_master_data import (
    build_transaher_barcode_24,
    format_transaher_decimal,
    format_transaher_postal_code,
    get_transaher_country_code,
    map_transaher_status_to_delivery_state,
    normalize_soap_base_url,
    parse_transaher_datetime,
    sanitize_transaher_field,
)
from ..models.transaher_request import (
    TransaherRequest,
    _find_all,
    _find_direct,
    _find_first,
    _localname,
    _parse_spanish_float,
)
from .common import TestDeliveryTransaherCommon

POST_PATH = "odoo.addons.delivery_transaher.models.transaher_request.requests.post"


@tagged("post_install", "-at_install")
class TestDeliveryTransaher(TestDeliveryTransaherCommon):
    def _mock_soap_response(self, xml_body, status_code=200):
        resp = MagicMock()
        resp.status_code = status_code
        resp.text = xml_body
        resp.content = xml_body.encode("utf-8")
        return resp

    def _xml_token_response(
        self, token="TOK-TRANSAHER-2026-VALID", err_code=0, err_desc=""
    ):
        return f"""<?xml version="1.0" encoding="utf-8"?>
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
          <s:Body>
            <executeResponse xmlns="MWSBridge.wsgettoken_services">
              <Response xmlns:a="MTRANS_WEB">
                <a:errCode>{err_code}</a:errCode>
                <a:errDesc>{err_desc}</a:errDesc>
                <a:Token>{token}</a:Token>
              </Response>
            </executeResponse>
          </s:Body>
        </s:Envelope>"""

    def _xml_alta_response(
        self,
        err_cod=0,
        err_dsc="",
        holding=0,
        seccion=10,
        centro=461,
        cod_exp="12685535",
    ):
        inner = f"""<?xml version="1.0" encoding="UTF-8"?>
        <MT_Return>
          <ErrCod>{err_cod}</ErrCod>
          <ErrDsc>{err_dsc}</ErrDsc>
          <Expediciones>
            <Expedicion>
              <Albaran_Ordenante>REF-01</Albaran_Ordenante>
              <Holding>{holding}</Holding>
              <Seccion>{seccion}</Seccion>
              <Centro>{centro}</Centro>
              <CodExpedicion>{cod_exp}</CodExpedicion>
              <Fecha_Expedicion>10/11/2026</Fecha_Expedicion>
              <Servicio>24H</Servicio>
              <Nombre_Destinatario>MANUEL FERNANDEZ GARCIA</Nombre_Destinatario>
              <Domicilio_Destinatario>ORTEGA Y GASSET 75</Domicilio_Destinatario>
              <Postal_Destinatario>28006</Postal_Destinatario>
              <Poblacion_Destinatario>MADRID</Poblacion_Destinatario>
              <Bultos>1</Bultos>
              <Total_Bultos>1</Total_Bultos>
              <Peso>25,000</Peso>
              <Area_Dis_Cod>28</Area_Dis_Cod>
              <Area_Dis_Dsc>MADRID CENTRO</Area_Dis_Dsc>
              <Centro_Destino>280 MADRID</Centro_Destino>
              <Expedicion_Ch>CH-9988</Expedicion_Ch>
            </Expedicion>
          </Expediciones>
        </MT_Return>"""
        return f"""<?xml version="1.0" encoding="utf-8"?>
        <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
          <SOAP-ENV:Body>
            <wsPrcSATSOAP.ExecuteResponse xmlns="MTRANS_WEB">
              <Respuesta>{escape(inner)}</Respuesta>
            </wsPrcSATSOAP.ExecuteResponse>
          </SOAP-ENV:Body>
        </SOAP-ENV:Envelope>"""

    def _xml_etiquetas_response(
        self, pdf_b64=None, has_error="false", key="", level_err=False
    ):
        data_val = pdf_b64 if pdf_b64 is not None else self.sample_pdf_b64
        lvl_msg = ""
        if level_err:
            lvl_msg = """
            <a:Messages>
              <a:TW_wsEtiExpSOAP_Response.Item>
                <a:Id>NotOwnerException</a:Id>
                <a:Type>ERROR</a:Type>
                <a:Description>No es propietario.</a:Description>
              </a:TW_wsEtiExpSOAP_Response.Item>
            </a:Messages>"""
        return f"""<?xml version="1.0" encoding="utf-8"?>
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
          <s:Body>
            <executeResponse xmlns="MWSBridge.wsetiexpsoap_services">
              <FileBase64String xmlns:a="MTRANS_WEB">
                <a:Name>AREti4en1GENE</a:Name>
                <a:Extension>pdf</a:Extension>
                <a:ContentType>application/pdf</a:ContentType>
                <a:Data>{data_val}</a:Data>
              </FileBase64String>
              <Response xmlns:a="MTRANS_WEB">
                <a:Name/>
                <a:Key>{key}</a:Key>
                <a:HasError>{has_error}</a:HasError>
                <a:Messages/>
                <a:Levels>
                  <a:TW_wsEtiExpSOAP_Response>
                    <a:Name>EXPEDICION</a:Name>
                    <a:Key>0.10.461.12685535</a:Key>
                    <a:HasError>{'true' if level_err else 'false'}</a:HasError>
                    {lvl_msg}
                    <a:Levels/>
                  </a:TW_wsEtiExpSOAP_Response>
                </a:Levels>
              </Response>
            </executeResponse>
          </s:Body>
        </s:Envelope>"""

    def _xml_baja_response(self, err_cod=0, err_desc="OK"):
        return f"""<?xml version="1.0" encoding="utf-8"?>
        <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
          <SOAP-ENV:Body>
            <wsExpBaja.ExecuteResponse xmlns="MTRANS_WEB">
              <Errcod>{err_cod}</Errcod>
              <Errdesc>{err_desc}</Errdesc>
            </wsExpBaja.ExecuteResponse>
          </SOAP-ENV:Body>
        </SOAP-ENV:Envelope>"""

    def _xml_tracking_response(
        self, situacion="ENTREGADO", err_cod=0, with_incidence=False
    ):
        inc_xml = ""
        if with_incidence:
            inc_xml = """
            <a:Incidencias>
              <a:sdtIncidencia>
                <a:FechaRegistro>2026-11-10 11:30</a:FechaRegistro>
                <a:TipoDescripcion>AUSENTE</a:TipoDescripcion>
                <a:CausaDescripcion>Destinatario ausente en reparto</a:CausaDescripcion>
                <a:DescripcionUno>Se deja aviso</a:DescripcionUno>
              </a:sdtIncidencia>
            </a:Incidencias>"""
        return f"""<?xml version="1.0" encoding="utf-8"?>
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
          <s:Body>
            <executeResponse xmlns="MWSBridge.wsinformaciontransporte_services">
              <InfoTransporteRsp xmlns:a="MWSBridge">
                <a:Mensajes>
                  <a:errCod>{err_cod}</a:errCod>
                  <a:errDsc/>
                </a:Mensajes>
                <a:Expediciones>
                  <a:sdtExpedicion>
                    <a:Holding>0</a:Holding>
                    <a:Seccion>10</a:Seccion>
                    <a:Centro>461</a:Centro>
                    <a:NroExpedicion>12685535</a:NroExpedicion>
                    <a:Situacion>{situacion}</a:Situacion>
                    <a:ChoferDescripcion>CARLOS GOMEZ</a:ChoferDescripcion>
                    <a:CentroDestino>280</a:CentroDestino>
                    <a:AreaDistribucionCodigo>28</a:AreaDistribucionCodigo>
                    <a:AreaDistribucionDescripcion>MADRID</a:AreaDistribucionDescripcion>
                    {inc_xml}
                    <a:Eventos>
                      <a:sdtEvento>
                        <a:FHRegistro>2026-11-10 08:15</a:FHRegistro>
                        <a:SituacionCodigo>REP</a:SituacionCodigo>
                        <a:SituacionDescripcion>EN REPARTO</a:SituacionDescripcion>
                        <a:TipoDescripcion>Salida a reparto</a:TipoDescripcion>
                      </a:sdtEvento>
                      <a:sdtEvento>
                        <a:FHRegistro>2026-11-10 13:45</a:FHRegistro>
                        <a:SituacionCodigo>ENT</a:SituacionCodigo>
                        <a:SituacionDescripcion>{situacion}</a:SituacionDescripcion>
                        <a:TipoDescripcion>Entrega conforme</a:TipoDescripcion>
                      </a:sdtEvento>
                    </a:Eventos>
                    <a:Bultos>
                      <a:sdtBulto>
                        <a:BultoRelativo>1</a:BultoRelativo>
                        <a:EAN>104610126855350012800601</a:EAN>
                        <a:SSCC>003841234567890001</a:SSCC>
                        <a:Peso>25,00</a:Peso>
                      </a:sdtBulto>
                    </a:Bultos>
                    <a:Importes>
                      <a:sdtImportes>
                        <a:ConceptoCod>1</a:ConceptoCod>
                        <a:ConceptoDsc>PORTES</a:ConceptoDsc>
                        <a:Divisa>EUR</a:Divisa>
                        <a:ImporteNeto>16,80</a:ImporteNeto>
                        <a:Situacion>FACTURADO</a:Situacion>
                        <a:FacturaCentro>461</a:FacturaCentro>
                        <a:FacturaSerie>26</a:FacturaSerie>
                        <a:FacturaNumero>004512</a:FacturaNumero>
                      </a:sdtImportes>
                    </a:Importes>
                  </a:sdtExpedicion>
                </a:Expediciones>
              </InfoTransporteRsp>
            </executeResponse>
          </s:Body>
        </s:Envelope>"""

    def test_01_barcode_24_decimal_format_and_datos_entrada(self):
        """Verify 24-digit barcode, PT CP rule, decimals, and 18-field Datosentrada."""
        # Exact example from Transaher Manual page 9:
        # 10 + 081 + 012685535 + 002 + 96600 + 01 = 100810126855350029660001
        barcode_es = build_transaher_barcode_24(
            centro_origen=81,
            cod_expedicion="12685535",
            bulto_num=2,
            postal_code="96600",
            country_code="ES",
        )
        self.assertEqual(len(barcode_es), 24)
        self.assertEqual(barcode_es, "100810126855350029660001")

        # Portugal rule: first 4 digits + '9' at position 22
        barcode_pt = build_transaher_barcode_24(
            centro_origen=461,
            cod_expedicion="99123",
            bulto_num=1,
            postal_code="1000-205",
            country_code="PT",
        )
        self.assertEqual(len(barcode_pt), 24)
        self.assertEqual(barcode_pt, "104610000991230011000901")

        # Country codes per Section 3.2 (011 = ES, 010 = PT)
        self.assertEqual(get_transaher_country_code(self.country_es), "011")
        self.assertEqual(get_transaher_country_code(self.country_pt), "010")

        # Comma decimal formatting & max_len enforcement
        self.assertEqual(format_transaher_decimal(10.0, max_len=8), "10")
        self.assertEqual(format_transaher_decimal(125.345, max_len=8), "125,345")
        self.assertEqual(format_transaher_decimal(12345.123, max_len=8), "12345,12")
        self.assertEqual(
            format_transaher_decimal(0.0, max_len=9, empty_if_zero=True), ""
        )

        # 18-field pipe-separated Datosentrada with pipe sanitization
        self.picking.write(
            {
                "transaher_obs_1": "Careful | Fragile chocolate",
                "transaher_insured_value": 250.5,
                "transaher_cod_amount": 99.95,
            }
        )
        datos = self.carrier._transaher_build_datos_entrada(
            picking=self.picking,
            gross_weight_kg=25.0,
            total_vol_m3=0.036,
            packages_qty=2,
        )
        parts = datos.split("|")
        self.assertEqual(len(parts), 18)
        self.assertEqual(parts[2], "011")  # Spain
        self.assertEqual(parts[3], "28006")
        self.assertEqual(parts[6], "REF-01")
        self.assertEqual(parts[7], "1")  # Portes pagados
        self.assertNotIn("|", parts[8])
        self.assertEqual(parts[10], "2")  # 2 bultos
        self.assertEqual(parts[11], "25")
        self.assertEqual(parts[12], "0,036")
        self.assertEqual(parts[13], "250,5")
        self.assertEqual(parts[14], "99,95")

    def test_02_tariff_rules_all_modes_and_constraints(self):
        """Test all 5 tariff calculation modes, surcharges, and range constraints."""
        cost, breakdown = self.tariff_rule._compute_rule_cost(
            chargeable_weight_kg=40.0,
            packages_qty=2,
            cod_amount=100.0,
            insured_value=200.0,
        )
        # Base 12.0 + excess (20kg * 0.25 = 5.0) = 17.0
        # Fuel 5% (0.85) + Insurance 1% (2.0) + COD 2% (2.0) -> Total = 21.85
        self.assertAlmostEqual(cost, 21.85, places=2)
        self.assertIn("Spain Mainland Excess Kg", breakdown)

        # Fixed mode with min_charge
        self.tariff_rule.write(
            {"rate_type": "fixed", "base_price": 8.0, "min_charge": 15.0}
        )
        c_fixed, _ = self.tariff_rule._compute_rule_cost(10.0, 1)
        self.assertAlmostEqual(c_fixed, 15.75, places=2)

        # per_kg mode
        self.tariff_rule.write(
            {
                "rate_type": "per_kg",
                "base_price": 5.0,
                "price_per_kg": 0.4,
                "min_charge": 0.0,
            }
        )
        c_kg, _ = self.tariff_rule._compute_rule_cost(25.0, 1)
        self.assertAlmostEqual(c_kg, 15.75, places=2)

        # per_100kg mode
        self.tariff_rule.write(
            {"rate_type": "per_100kg", "base_price": 10.0, "price_per_kg": 12.0}
        )
        c_100, _ = self.tariff_rule._compute_rule_cost(210.0, 1)
        # (10 + 3*12 = 46) * 1.05 = 48.30
        self.assertAlmostEqual(c_100, 48.30, places=2)

        # per_package mode
        self.tariff_rule.write(
            {"rate_type": "per_package", "base_price": 4.0, "price_per_package": 8.0}
        )
        c_pkg, _ = self.tariff_rule._compute_rule_cost(50.0, 3)
        # (4 + 3*8 = 28) * 1.05 = 29.40
        self.assertAlmostEqual(c_pkg, 29.40, places=2)

        with self.assertRaises(ValidationError):
            self.tariff_rule.write({"min_weight": 300.0, "max_weight": 50.0})
        with self.assertRaises(ValidationError):
            self.tariff_rule.write({"min_packages": 5, "max_packages": 2})

    def test_03_rate_shipment_wizard_and_free_for_customer(self):
        """Test SO rating, ChooseDeliveryCarrier breakdown, and free_for_customer."""
        res = self.carrier.transaher_rate_shipment(self.sale_order)
        self.assertTrue(res["success"])
        self.assertGreater(res["price"], 0.0)
        expected_cost = res["price"]
        self.assertAlmostEqual(
            self.sale_order.transaher_estimated_cost, expected_cost, places=2
        )

        wiz = self.env["choose.delivery.carrier"].create(
            {
                "order_id": self.sale_order.id,
                "carrier_id": self.carrier.id,
            }
        )
        wiz._get_delivery_rate()
        self.assertTrue(wiz.is_transaher_carrier)
        self.assertAlmostEqual(wiz.transaher_estimated_cost, expected_cost, places=2)

        # Free for customer keeps internal cost on sale order
        self.carrier.transaher_free_for_customer = True
        res_free = self.carrier.transaher_rate_shipment(self.sale_order)
        self.assertTrue(res_free["success"])
        self.assertEqual(res_free["price"], 0.0)
        self.assertAlmostEqual(
            self.sale_order.transaher_estimated_cost, expected_cost, places=2
        )
        self.carrier.transaher_free_for_customer = False

    @patch(POST_PATH)
    def test_04_token_auth_caching_and_auto_renewal_on_expiry(self, mock_post):
        """Test wsgetToken caching and automatic renewal on expired token (code 2)."""
        mock_post.return_value = self._mock_soap_response(
            self._xml_token_response(token="TOKEN-INITIAL-1111")
        )
        notif = self.carrier.action_test_transaher_connection()
        self.assertEqual(notif["params"]["type"], "success")
        self.assertEqual(mock_post.call_count, 1)

        # Second call reuses cached token without hitting network
        client = self.carrier._transaher_get_client()
        tok2 = client.get_token(force_refresh=False)
        self.assertEqual(tok2, "TOKEN-INITIAL-1111")
        self.assertEqual(mock_post.call_count, 1)

        # Simulate expired token (Key=2) -> auto refreshes token and retries!
        expired_lbl_resp = self._mock_soap_response(
            self._xml_etiquetas_response(pdf_b64="", has_error="true", key="2")
        )
        fresh_tok_resp = self._mock_soap_response(
            self._xml_token_response(token="TOKEN-RENEWED-2222")
        )
        ok_lbl_resp = self._mock_soap_response(self._xml_etiquetas_response())
        mock_post.side_effect = [expired_lbl_resp, fresh_tok_resp, ok_lbl_resp]

        lbl_data = client.get_labels(
            [
                {
                    "holding": 0,
                    "seccion": 10,
                    "centro": 461,
                    "codigo": "12685535",
                    "bultos": "-1",
                }
            ]
        )
        self.assertEqual(lbl_data["data"], self.sample_pdf_b64)
        self.assertEqual(
            self.carrier.sudo().transaher_cached_token, "TOKEN-RENEWED-2222"
        )

    @patch(POST_PATH)
    def test_05_send_shipping_alta_labels_and_package_barcodes(self, mock_post):
        """Test picking submission, 24-digit barcodes, labels, and OCA fields."""
        pkg = self.env["stock.quant.package"].create(
            {
                "name": "PACK-TRN-001",
                "package_type_id": self.package_type_box.id,
            }
        )
        self.picking.move_line_ids.write({"result_package_id": pkg.id})

        # OCA delivery_package_number computes number_of_packages from physical packages
        self.assertEqual(self.picking.number_of_packages, 1)
        # OCA stock_picking_volume computes picking.volume (10 * 0.5 * 0.3 * 0.2 = 0.30)
        self.assertAlmostEqual(self.picking.volume, 0.30, places=3)

        mock_post.side_effect = [
            self._mock_soap_response(self._xml_alta_response(cod_exp="12685535")),
            self._mock_soap_response(self._xml_token_response()),
            self._mock_soap_response(self._xml_etiquetas_response()),
        ]
        self.picking.send_to_shipper()

        self.assertEqual(self.picking.carrier_tracking_ref, "12685535")
        self.assertEqual(self.picking.transaher_cod_expedicion, "12685535")
        self.assertEqual(self.picking.transaher_expedition_key, "0.10.461.12685535")
        # OCA delivery_state fields set on send_shipping
        self.assertEqual(self.picking.delivery_state, "shipping_recorded_in_carrier")
        self.assertTrue(self.picking.date_shipped)
        self.assertEqual(self.picking.transaher_centro_destino, "280 MADRID")
        self.assertEqual(pkg.transaher_barcode, "104610126855350012800601")

        # Verify Datosentrada sent OCA number_of_packages (1), weight (25,5), vol (0,3)
        alta_call_xml = (
            mock_post.call_args_list[0].kwargs.get("data", b"").decode("utf-8")
        )
        self.assertIn("|1|25,5|0,3|", alta_call_xml)

        attachments = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "stock.picking"),
                ("res_id", "=", self.picking.id),
                ("name", "ilike", "Transaher_Label_%"),
            ]
        )
        self.assertTrue(attachments)

    @mute_logger("odoo.addons.delivery_transaher.models.delivery_carrier")
    @patch(POST_PATH)
    def test_06_label_fallback_qweb_and_not_owner_error(self, mock_post):
        """Test fallback to local QWeb 24-digit barcode label and ws_only errors."""
        self.carrier.sudo().write(
            {
                "transaher_cached_token": "VALID-TOK",
                "transaher_token_valid_until": "2099-12-31 23:59:59",
            }
        )
        # Partial/expedition error NotOwnerException (Section 6.4) with empty Data
        err_lbl_resp = self._mock_soap_response(
            self._xml_etiquetas_response(pdf_b64="", has_error="true", level_err=True)
        )
        mock_post.side_effect = [
            self._mock_soap_response(self._xml_alta_response(cod_exp="77788899")),
            err_lbl_resp,
        ]
        # In ws_with_fallback mode, falls back cleanly to local QWeb PDF label
        ship_res = self.carrier.transaher_send_shipping(self.picking)
        self.assertEqual(ship_res[0]["tracking_number"], "77788899")

        # In ws_only mode, NotOwnerException raises UserError
        self.carrier.transaher_label_mode = "ws_only"
        mock_post.side_effect = None
        mock_post.return_value = err_lbl_resp
        with self.assertRaises(UserError):
            self.picking.action_transaher_get_label()
        self.carrier.transaher_label_mode = "ws_with_fallback"

        # Direct QWeb label report action works cleanly
        rep_act = self.picking.action_transaher_print_local_label()
        self.assertEqual(rep_act["type"], "ir.actions.report")

    @patch(POST_PATH)
    def test_07_tracking_events_incidences_cost_audit_and_oca_cron(self, mock_post):
        """Test OCA `tracking_state_update` and `_update_delivery_state`."""
        pkg = self.env["stock.quant.package"].create(
            {"name": "PACK-TRN-002", "package_type_id": self.package_type_box.id}
        )
        self.picking.move_line_ids.write({"result_package_id": pkg.id})
        self.picking.write(
            {
                "state": "done",
                "date_done": "2026-11-10 09:00:00",
                "carrier_tracking_ref": "12685535",
                "transaher_cod_expedicion": "12685535",
                "transaher_centro": 461,
                "transaher_estimated_cost": 15.00,
                "delivery_state": "in_transit",
            }
        )
        self.carrier.sudo().write(
            {
                "transaher_cached_token": "VALID-TOK",
                "transaher_token_valid_until": "2099-12-31 23:59:59",
            }
        )

        # 1. Incidence detection via standard OCA `tracking_state_update()`
        mock_post.return_value = self._mock_soap_response(
            self._xml_tracking_response(situacion="EN REPARTO", with_incidence=True)
        )
        self.picking.tracking_state_update()
        self.assertEqual(self.picking.delivery_state, "incident")
        self.assertTrue(self.picking.transaher_has_incidence)
        self.assertIn("AUSENTE", self.picking.transaher_incidence_text)
        self.assertIn("AUSENTE", self.picking.tracking_state_history)

        # 2. Delivered + invoiced costs via OCA cron `_update_delivery_state()`
        mock_post.return_value = self._mock_soap_response(
            self._xml_tracking_response(situacion="ENTREGADO", with_incidence=False)
        )
        self.env["stock.picking"]._update_delivery_state()
        self.assertEqual(self.picking.delivery_state, "customer_delivered")
        self.assertTrue(self.picking.date_delivered)
        self.assertIn("[ENT] ENTREGADO", self.picking.tracking_state)
        self.assertIn("Salida a reparto", self.picking.tracking_state_history)
        self.assertTrue(self.picking.tracking_json)
        self.assertEqual(pkg.transaher_sscc, "003841234567890001")
        self.assertAlmostEqual(self.picking.transaher_invoiced_cost, 16.80, places=2)
        self.assertAlmostEqual(self.picking.transaher_cost_difference, 1.80, places=2)
        self.assertEqual(self.picking.transaher_invoice_number, "461-26-004512")

    @patch(POST_PATH)
    def test_08_cancel_shipment_baja_rules_and_return_label(self, mock_post):
        """Test awsExpBaja cancellation rules with OCA `delivery_state` and returns."""
        self.picking.write(
            {
                "carrier_tracking_ref": "12685535",
                "transaher_cod_expedicion": "12685535",
                "transaher_centro": 461,
                "delivery_state": "customer_delivered",
            }
        )
        # Cannot cancel an already delivered expedition (Section 4.1)
        with self.assertRaises(UserError):
            self.picking.cancel_shipment()

        # Server returning Errcod=2 (invalid status) raises UserError
        self.picking.delivery_state = "shipping_recorded_in_carrier"
        mock_post.return_value = self._mock_soap_response(
            self._xml_baja_response(
                err_cod=2, err_desc="Situacion de expedicion incorrecta"
            )
        )
        with self.assertRaises(UserError):
            self.picking.cancel_shipment()

        # Successful cancellation updates OCA delivery_state to canceled_shipment
        mock_post.return_value = self._mock_soap_response(
            self._xml_baja_response(err_cod=0)
        )
        self.picking.cancel_shipment()
        self.assertFalse(self.picking.carrier_tracking_ref)
        self.assertEqual(self.picking.delivery_state, "canceled_shipment")
        self.assertFalse(self.picking.date_shipped)
        self.assertFalse(self.picking.date_delivered)

        # Standard Odoo print_return_label() flow via can_generate_return
        self.assertTrue(self.carrier.can_generate_return)
        self.carrier.sudo().write(
            {
                "transaher_cached_token": "VALID-TOK",
                "transaher_token_valid_until": "2099-12-31 23:59:59",
            }
        )
        mock_post.side_effect = [
            self._mock_soap_response(self._xml_alta_response(cod_exp="99887766")),
            self._mock_soap_response(self._xml_etiquetas_response()),
        ]
        self.picking.print_return_label()
        self.picking.invalidate_recordset(["return_label_ids"])
        self.assertTrue(self.picking.return_label_ids)
        self.assertIn(
            "Transaher_Return_99887766", self.picking.return_label_ids[0].name
        )

    @mute_logger("odoo.addons.delivery_transaher.models.transaher_request")
    @patch(POST_PATH)
    def test_09_manifest_wizard_awsmnfprtsoap_and_soap_faults(self, mock_post):
        """Test Daily Manifest wizard (awsmnfprtsoap) and SOAP/network errors."""
        manifest_inner = """<?xml version="1.0" encoding="UTF-8"?>
        <MT_Return>
          <ErrCod>0</ErrCod>
          <ErrDsc/>
          <Expediciones>
            <Expedicion>
              <Holding>0</Holding>
              <Seccion>10</Seccion>
              <Centro>461</Centro>
              <CodExpedicion>12685535</CodExpedicion>
              <Albaran_Ordenante>WH/OUT/0001</Albaran_Ordenante>
              <Nombre_Destinatario>MANUEL FERNANDEZ GARCIA</Nombre_Destinatario>
              <Domicilio_Destinatario>ORTEGA Y GASSET 75</Domicilio_Destinatario>
              <Postal_Destinatario>28006</Postal_Destinatario>
              <Poblacion_Destinatario>MADRID</Poblacion_Destinatario>
              <Total_Bultos>2</Total_Bultos>
              <Peso>25,000</Peso>
            </Expedicion>
          </Expediciones>
        </MT_Return>"""
        manifest_soap = f"""<?xml version="1.0" encoding="utf-8"?>
        <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
          <SOAP-ENV:Body>
            <wsMnfPrtSOAP.ExecuteResponse xmlns="MTRANS_WEB">
              <Respuesta>{escape(manifest_inner)}</Respuesta>
            </wsMnfPrtSOAP.ExecuteResponse>
          </SOAP-ENV:Body>
        </SOAP-ENV:Envelope>"""

        mock_post.return_value = self._mock_soap_response(manifest_soap)
        act = self.carrier.action_open_manifest_wizard()
        wiz = (
            self.env[act["res_model"]]
            .with_context(**act["context"])
            .create({"source_mode": "ws_only"})
        )
        wiz.action_generate_manifest_pdf()
        self.assertTrue(wiz.pdf_file)
        self.assertIn("Transaher_Manifest_", wiz.pdf_filename)

        # SOAP Fault handling
        fault_xml = """<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
          <soap:Body>
            <soap:Fault>
              <faultcode>soap:Server</faultcode>
              <faultstring>Internal GeneXus Error</faultstring>
            </soap:Fault>
          </soap:Body>
        </soap:Envelope>"""
        mock_post.return_value = self._mock_soap_response(fault_xml, status_code=500)
        with self.assertRaises(UserError):
            wiz.action_generate_manifest_pdf()

        # Network ConnectionError handling
        mock_post.side_effect = requests.exceptions.ConnectionError(
            "Connection refused"
        )
        with self.assertRaises(UserError):
            wiz.action_generate_manifest_pdf()

    def test_10_url_normalization_token_invalidation_and_shipping_insurance(self):
        """Test URL normalization, token cache invalidation, and shipping_insurance."""
        # 1. URL normalization strips accidental .aspx?wsdl / .svc?singlewsdl suffixes
        self.assertEqual(
            normalize_soap_base_url(
                "https://clientes.transaher.es/mclient_test/awsprcsatsoap.aspx?wsdl"
            ),
            "https://clientes.transaher.es/mclient_test",
        )
        self.assertEqual(
            normalize_soap_base_url(
                "https://clientes.transaher.es/mbridge/wsgetToken.svc?singlewsdl"
            ),
            "https://clientes.transaher.es/mbridge",
        )

        # 2. Token cache invalidation when switching prod_environment or credentials
        self.carrier.sudo().write(
            {
                "transaher_cached_token": "TEST-ENV-TOK",
                "transaher_token_valid_until": "2099-12-31 23:59:59",
            }
        )
        self.assertEqual(self.carrier.sudo().transaher_cached_token, "TEST-ENV-TOK")
        self.carrier.write({"prod_environment": True})
        self.assertFalse(self.carrier.sudo().transaher_cached_token)
        self.assertFalse(self.carrier.sudo().transaher_token_valid_until)
        self.carrier.write({"prod_environment": False})

        # 3. Odoo shipping_insurance percentage populates Field 14 of Datosentrada
        self.assertTrue(self.carrier.supports_shipping_insurance)
        self.carrier.shipping_insurance = 50
        self.picking.transaher_insured_value = 0.0
        # sale_order has 10 units * 32.0 = 320.0 untaxed; 50% insured = 160.0 -> "160"
        datos = self.carrier._transaher_build_datos_entrada(
            picking=self.picking,
            gross_weight_kg=25.0,
            total_vol_m3=0.036,
            packages_qty=1,
        )
        self.assertEqual(datos.split("|")[13], "160")
        self.carrier.shipping_insurance = 0

    @patch(POST_PATH)
    def test_11_oca_manual_package_number_and_volumetric_chargeable_weight(
        self, mock_post
    ):
        """Test OCA `number_of_packages` and OCA `volume` volumetric weight."""
        # Without physical packages, set OCA `number_of_packages` = 3 on the picking
        self.picking.number_of_packages = 3

        # 10 units * (0.50m * 0.30m * 0.20m = 0.03 m³) = 0.30 m³ (stock_picking_volume)
        gross_w, vol_m3, pkgs_qty = self.carrier._transaher_prepare_picking_metrics(
            self.picking
        )
        self.assertAlmostEqual(gross_w, 25.0, places=2)
        self.assertAlmostEqual(vol_m3, 0.30, places=3)
        self.assertEqual(pkgs_qty, 3)

        # Volumetric weight = 0.30 m³ * 250 kg/m³ = 75.0 kg (> 25.0 kg gross weight)
        self.picking.action_transaher_calculate_rate()
        self.assertAlmostEqual(self.picking.transaher_chargeable_weight, 75.0, places=2)

        # Send shipping generates 3 24-digit barcodes (001, 002, 003) and sends Bultos=3
        mock_post.side_effect = [
            self._mock_soap_response(self._xml_alta_response(cod_exp="55566677")),
            self._mock_soap_response(self._xml_token_response()),
            self._mock_soap_response(self._xml_etiquetas_response()),
        ]
        self.picking.send_to_shipper()
        barcodes = [b.strip() for b in self.picking.transaher_barcodes.split(",")]
        self.assertEqual(len(barcodes), 3)
        self.assertEqual(barcodes[0], "104610555666770012800601")
        self.assertEqual(barcodes[1], "104610555666770022800601")
        self.assertEqual(barcodes[2], "104610555666770032800601")
        label_items = self.picking._get_transaher_label_items()
        self.assertEqual(len(label_items), 3)

    def test_12_master_data_status_mapping_postal_and_datetime_helpers(self):
        """Test all branches of master data formatting, status mapping, and dates."""
        self.assertEqual(normalize_soap_base_url("", fallback=""), "")
        self.assertEqual(sanitize_transaher_field(False), "")
        self.assertEqual(
            format_transaher_decimal(123.0, max_len=3, max_decimals=2), "123"
        )
        self.assertEqual(
            format_transaher_decimal(123456.0, max_len=4, max_decimals=2), "1234"
        )
        self.assertEqual(get_transaher_country_code(False), "011")
        self.assertEqual(get_transaher_country_code("11"), "011")

        self.assertEqual(
            format_transaher_postal_code(
                "1000-205", country_code="PT", for_barcode=False
            ),
            "1000",
        )
        self.assertEqual(
            format_transaher_postal_code("801", country_code="PT", for_barcode=False),
            "0801",
        )
        self.assertEqual(
            format_transaher_postal_code("8001", country_code="ES", for_barcode=False),
            "08001",
        )
        self.assertEqual(
            format_transaher_postal_code("AB-CD", country_code="GB", for_barcode=False),
            "AB-CD",
        )
        self.assertEqual(
            format_transaher_postal_code("", country_code="PT", for_barcode=True),
            "00009",
        )

        self.assertEqual(
            map_transaher_status_to_delivery_state("", ""),
            "shipping_recorded_in_carrier",
        )
        self.assertEqual(
            map_transaher_status_to_delivery_state("ANULADO", ""),
            "canceled_shipment",
        )
        self.assertEqual(
            map_transaher_status_to_delivery_state("AUSENTE EN REPARTO", ""),
            "incident",
        )
        self.assertEqual(
            map_transaher_status_to_delivery_state("ENTREGADO", "", is_return=True),
            "warehouse_delivered",
        )
        self.assertEqual(
            map_transaher_status_to_delivery_state("EN TRANSITO", ""),
            "in_transit",
        )
        self.assertEqual(
            map_transaher_status_to_delivery_state("DOCUMENTADO", ""),
            "shipping_recorded_in_carrier",
        )
        self.assertEqual(
            map_transaher_status_to_delivery_state("OTRO ESTADO", ""),
            "in_transit",
        )

        self.assertIsNone(parse_transaher_datetime(""))
        self.assertEqual(
            parse_transaher_datetime("10/11/2026 14:30"),
            datetime(2026, 11, 10, 14, 30),
        )
        self.assertIsNone(parse_transaher_datetime("invalid-date-format"))

    @mute_logger("odoo.addons.delivery_transaher.models.transaher_request")
    @patch(POST_PATH)
    def test_13_xml_helpers_soap_errors_and_sdt_entrega_parsing(self, mock_post):
        """Test TransaherRequest XML helpers, prod URLs, errors, and sdtEntrega."""
        self.assertEqual(_localname(None), "")
        self.assertEqual(_localname("ns:Node"), "Node")
        self.assertIsNone(_find_first(None, "x"))
        self.assertIsNone(_find_direct(None, "x"))
        self.assertEqual(_find_all(None, "x"), [])
        self.assertAlmostEqual(_parse_spanish_float("1.234,56"), 1234.56, places=2)
        self.assertEqual(_parse_spanish_float("not-a-number"), 0.0)
        self.assertEqual(TransaherRequest._mask_xml_for_logging(""), "")
        self.assertEqual(
            TransaherRequest._parse_labels_response_node(None),
            (False, "", [], []),
        )

        client = self.carrier._transaher_get_client()
        # Production environment URLs & credentials
        self.carrier.prod_environment = True
        self.assertIn("/mclient", client._get_mclient_base_url())
        self.assertIn("/mbridge", client._get_mbridge_base_url())
        self.assertEqual(client._get_credentials(), (99999, "prod-secret-psw"))

        # Non-numeric client code & missing credentials
        self.carrier.transaher_client_code_prod = "ABC"
        with self.assertRaises(UserError):
            client._get_credentials()
        self.carrier.write(
            {
                "transaher_client_code_prod": False,
                "transaher_client_code_test": False,
            }
        )
        with self.assertRaises(UserError):
            client._get_credentials()
        self.carrier.write(
            {
                "prod_environment": False,
                "transaher_client_code_test": "12345",
                "transaher_client_code_prod": "99999",
            }
        )

        # HTTP 502 non-XML response & HTTP 200 empty response
        bad_resp = MagicMock(status_code=502, text="<<<Bad", content=b"<<<Bad")
        mock_post.return_value = bad_resp
        with self.assertRaises(UserError):
            client.get_token(force_refresh=True)

        empty_resp = MagicMock(status_code=200, text="", content=b"")
        mock_post.return_value = empty_resp
        with self.assertRaises(UserError):
            client.get_token(force_refresh=True)

        # Token non-integer errCode & double token expiry
        mock_post.return_value = self._mock_soap_response(
            self._xml_token_response(token="", err_code="BAD", err_desc="")
        )
        with self.assertRaises(UserError):
            client.get_token(force_refresh=True)

        self.carrier.sudo().write(
            {
                "transaher_cached_token": "TOK-1",
                "transaher_token_valid_until": "2099-12-31 23:59:59",
            }
        )
        with self.assertRaises(UserError):
            mock_post.side_effect = [
                self._mock_soap_response(self._xml_token_response(token="TOK-2")),
            ]
            client._execute_with_token_retry(
                lambda _tok: {"_token_expired": True, "_token_error_msg": "Expired"}
            )
        mock_post.side_effect = None

        # create_expedition error branches & direct MT_Return without Respuesta
        mock_post.return_value = self._mock_soap_response(
            "<Envelope><Body/></Envelope>"
        )
        with self.assertRaises(UserError):
            client.create_expedition("A|B")

        mock_post.return_value = self._mock_soap_response(
            "<Envelope><Body><MT_Return><ErrCod>BAD</ErrCod></MT_Return></Body></Envelope>"
        )
        with self.assertRaises(UserError):
            client.create_expedition("A|B")

        mock_post.return_value = self._mock_soap_response(
            "<Envelope><Body><MT_Return><ErrCod>0</ErrCod><Expediciones/></MT_Return></Body></Envelope>"
        )
        with self.assertRaises(UserError):
            client.create_expedition("A|B")

        mock_post.return_value = self._mock_soap_response(
            "<Envelope><Body><MT_Return><ErrCod>0</ErrCod>"
            "<Expediciones><Expedicion><CodExpedicion/></Expedicion></Expediciones>"
            "</MT_Return></Body></Envelope>"
        )
        with self.assertRaises(UserError):
            client.create_expedition("A|B")

        # cancel_expedition invalid expcod & non-numeric Errcod
        with self.assertRaises(UserError):
            client.cancel_expedition(0, 10, 461, "---")
        mock_post.return_value = self._mock_soap_response(
            self._xml_baja_response(err_cod="BAD", err_desc="Custom err")
        )
        with self.assertRaises(UserError):
            client.cancel_expedition(0, 10, 461, "12685535")

        # get_labels empty input, posicion_inicial & global Messages
        with self.assertRaises(UserError):
            client.get_labels([])

        self.carrier.sudo().write(
            {
                "transaher_cached_token": "VALID-TOK",
                "transaher_token_valid_until": "2099-12-31 23:59:59",
            }
        )
        global_msg_lbl = """<?xml version="1.0" encoding="utf-8"?>
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
          <s:Body>
            <executeResponse xmlns="MWSBridge.wsetiexpsoap_services">
              <FileBase64String xmlns:a="MTRANS_WEB">
                <a:Extension>pdf</a:Extension>
                <a:Data/>
              </FileBase64String>
              <Response xmlns:a="MTRANS_WEB">
                <a:Key>99</a:Key>
                <a:HasError>true</a:HasError>
                <a:Messages>
                  <a:TW_wsEtiExpSOAP_Response.Item>
                    <a:Id>E99</a:Id>
                    <a:Type>ERROR</a:Type>
                    <a:Description>Global label failure</a:Description>
                  </a:TW_wsEtiExpSOAP_Response.Item>
                </a:Messages>
              </Response>
            </executeResponse>
          </s:Body>
        </s:Envelope>"""
        mock_post.return_value = self._mock_soap_response(global_msg_lbl)
        with self.assertRaises(UserError):
            client.get_labels(
                [
                    {
                        "holding": 0,
                        "seccion": 10,
                        "centro": 461,
                        "codigo": "1",
                        "bultos": "",
                    }
                ],
                posicion_inicial="2",
            )

        # get_tracking_info date filters, token retry, sdtEntrega, and error code
        trk_entrega_xml = """<?xml version="1.0" encoding="utf-8"?>
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
          <s:Body>
            <executeResponse xmlns="MWSBridge.wsinformaciontransporte_services">
              <InfoTransporteRsp xmlns:a="MWSBridge">
                <a:Mensajes><a:errCod>0</a:errCod><a:errDsc/></a:Mensajes>
                <a:Expediciones>
                  <a:sdtExpedicion>
                    <a:NroExpedicion>12685535</a:NroExpedicion>
                    <a:Situacion>EN REPARTO</a:Situacion>
                    <a:Entregas>
                      <a:sdtEntrega>
                        <a:Situacion>REPARTO</a:Situacion>
                        <a:Eventos>
                          <a:sdtEvento>
                            <a:FHRegistro>2026-11-10 10:00</a:FHRegistro>
                            <a:SituacionCodigo>R1</a:SituacionCodigo>
                            <a:SituacionDescripcion>Reparto</a:SituacionDescripcion>
                          </a:sdtEvento>
                        </a:Eventos>
                        <a:Incidencias>
                          <a:sdtIncidencia>
                            <a:FechaRegistro>2026-11-10 11:00</a:FechaRegistro>
                            <a:TipoDescripcion>DIRECCION</a:TipoDescripcion>
                          </a:sdtIncidencia>
                        </a:Incidencias>
                      </a:sdtEntrega>
                    </a:Entregas>
                  </a:sdtExpedicion>
                </a:Expediciones>
              </InfoTransporteRsp>
            </executeResponse>
          </s:Body>
        </s:Envelope>"""
        trk_expired = self._xml_tracking_response(err_cod=2)
        mock_post.side_effect = [
            self._mock_soap_response(trk_expired),
            self._mock_soap_response(self._xml_token_response(token="TOK-TRK")),
            self._mock_soap_response(trk_entrega_xml),
        ]
        trk_res = client.get_tracking_info(
            holding=0,
            seccion=10,
            centro=461,
            numero_expedicion="12685535",
            albaran_ordenante="REF-01",
            fecha_desde="2026-11-01",
            fecha_hasta="2026-11-12",
        )
        self.assertEqual(len(trk_res["expediciones"][0]["deliveries"]), 1)
        self.assertEqual(len(trk_res["expediciones"][0]["events"]), 1)
        self.assertEqual(len(trk_res["expediciones"][0]["incidences"]), 1)
        mock_post.side_effect = None

        mock_post.return_value = self._mock_soap_response(
            self._xml_tracking_response(err_cod="BAD")
        )
        with self.assertRaises(UserError):
            client.get_tracking_info(numero_expedicion="12685535")

        # get_manifest_data direct MT_Return with non-numeric ErrCod
        mock_post.return_value = self._mock_soap_response(
            "<Envelope><Body><MT_Return><ErrCod>BAD</ErrCod></MT_Return></Body></Envelope>"
        )
        with self.assertRaises(UserError):
            client.get_manifest_data("202611100000", "202611102359")

    def test_14_package_types_tariff_filters_and_sale_order_delivery_line(self):
        """Test StockPackageType onchange/write, tariff filters, and delivery line."""
        pkg_type = self.env["stock.package.type"].create(
            {
                "name": "Transaher Custom Type",
                "package_carrier_type": "transaher",
                "transaher_packaging_code": "CAJ",
            }
        )
        self.assertEqual(pkg_type.shipper_package_code, "CAJ")
        pkg_type.transaher_packaging_code = "MED"
        pkg_type._onchange_transaher_packaging_code()
        self.assertEqual(pkg_type.shipper_package_code, "MED")
        pkg_type.write({"transaher_packaging_code": "EUR"})
        self.assertEqual(pkg_type.shipper_package_code, "EUR")

        # Non-Transaher carrier capability fallbacks & wizard reset
        fixed_carrier = self.env["delivery.carrier"].create(
            {
                "name": "Fixed Carrier Test",
                "delivery_type": "fixed",
                "product_id": self.delivery_product.id,
                "fixed_price": 5.0,
            }
        )
        self.assertFalse(fixed_carrier.can_generate_return)
        self.assertNotEqual(
            fixed_carrier._get_delivery_label_prefix(), "Transaher_Label"
        )
        self.assertNotEqual(fixed_carrier.get_return_label_prefix(), "Transaher_Return")
        self.assertEqual(
            self.carrier._transaher_get_default_custom_package_code(), "BUL"
        )

        wiz_fixed = self.env["choose.delivery.carrier"].create(
            {"order_id": self.sale_order.id, "carrier_id": fixed_carrier.id}
        )
        wiz_fixed._get_delivery_rate()
        self.assertFalse(wiz_fixed.is_transaher_carrier)
        self.assertEqual(wiz_fixed.transaher_estimated_cost, 0.0)

        # Confirm ChooseDeliveryCarrier for Transaher -> calls _create_delivery_line
        wiz_trn = self.env["choose.delivery.carrier"].create(
            {"order_id": self.sale_order.id, "carrier_id": self.carrier.id}
        )
        wiz_trn._get_delivery_rate()
        wiz_trn.button_confirm()
        self.assertTrue(self.sale_order.order_line.filtered("is_delivery"))

        # Tariff rule filter mismatches
        self.tariff_rule.write(
            {
                "min_weight": 5.0,
                "max_weight": 200.0,
                "min_packages": 1,
                "max_packages": 5,
            }
        )
        pt_partner = self.env["res.partner"].create(
            {
                "name": "PT Client",
                "street": "Rua Augusta 10",
                "city": "Lisboa",
                "zip": "1100-053",
                "country_id": self.country_pt.id,
            }
        )
        self.assertFalse(
            self.tariff_rule._match_destination_and_shipment(pt_partner, 20.0, 2)
        )
        other_state = self.env["res.country.state"].create(
            {"name": "ValenciaTest", "code": "VT", "country_id": self.country_es.id}
        )
        val_partner = self.env["res.partner"].create(
            {
                "name": "Val Client",
                "street": "Colon 1",
                "city": "Valencia",
                "zip": "46001",
                "state_id": other_state.id,
                "country_id": self.country_es.id,
            }
        )
        self.assertFalse(
            self.tariff_rule._match_destination_and_shipment(val_partner, 20.0, 2)
        )
        bad_zip_partner = self.env["res.partner"].create(
            {
                "name": "Bad Zip",
                "street": "Calle 1",
                "city": "Madrid",
                "zip": "08001",
                "state_id": self.state_madrid.id,
                "country_id": self.country_es.id,
            }
        )
        self.assertFalse(
            self.tariff_rule._match_destination_and_shipment(bad_zip_partner, 20.0, 2)
        )
        self.assertFalse(
            self.tariff_rule._match_destination_and_shipment(self.partner, 2.0, 2)
        )
        self.assertFalse(
            self.tariff_rule._match_destination_and_shipment(self.partner, 250.0, 2)
        )
        self.tariff_rule.min_packages = 2
        self.assertFalse(
            self.tariff_rule._match_destination_and_shipment(self.partner, 20.0, 1)
        )
        self.assertFalse(
            self.tariff_rule._match_destination_and_shipment(self.partner, 20.0, 9)
        )

    def test_15_carrier_dimensions_uom_portes_observations_and_metrics(self):
        """Test UoM conversions, package dimensions, Portes/Incoterm, and fallbacks."""
        self.assertEqual(self.carrier._transaher_convert_weight_to_kg(0), 0.0)
        self.assertEqual(self.carrier._transaher_convert_volume_to_m3(0), 0.0)
        self.assertEqual(self.carrier._transaher_convert_dimension_to_cm(0), 0)

        # UoM conversion branches when system UoMs are lbs, ft³, and mm
        icp = self.env["ir.config_parameter"].sudo()
        icp.set_param("product.weight_in_lbs", "1")
        icp.set_param("product.volume_in_cubic_feet", "1")
        mm_uom = self.env.ref("uom.product_uom_millimeter", raise_if_not_found=False)
        if mm_uom:
            icp.set_param("product.volume_in_cubic_feet", "1")
        self.assertGreater(self.carrier._transaher_convert_weight_to_kg(10.0), 0.0)
        self.assertGreater(self.carrier._transaher_convert_volume_to_m3(10.0), 0.0)
        self.assertGreater(self.carrier._transaher_convert_dimension_to_cm(100), 0)
        icp.set_param("product.weight_in_lbs", "0")
        icp.set_param("product.volume_in_cubic_feet", "0")

        # Dimension fallbacks for EUR, MED, SOB, and BUL without explicit dimensions
        for code, expected_l in [("EUR", 120), ("MED", 80), ("SOB", 35), ("BUL", 40)]:
            p_type = self.env["stock.package.type"].create(
                {
                    "name": f"NoDims {code}",
                    "package_carrier_type": "transaher",
                    "transaher_packaging_code": code,
                }
            )
            l_cm, _w, _h, res_code = self.carrier._transaher_get_package_dimensions_cm(
                p_type
            )
            self.assertEqual(l_cm, expected_l)
            self.assertEqual(res_code, code)

        # Portes resolution: picking override & Incoterm EXW -> '2'
        self.picking.transaher_portes = "2"
        self.assertEqual(
            self.carrier._transaher_resolve_portes_code(picking=self.picking), "2"
        )
        self.picking.transaher_portes = False
        exw = self.env.ref("account.incoterm_EXW", raise_if_not_found=False)
        if exw:
            self.sale_order.incoterm = exw
            self.assertEqual(
                self.carrier._transaher_resolve_portes_code(picking=self.picking), "2"
            )
            self.assertEqual(
                self.carrier._transaher_resolve_portes_code(order=self.sale_order), "2"
            )

        # Observations splitting: empty, >70 chars with spaces, and 80-char word
        self.assertEqual(
            self.carrier._transaher_split_observations(fallback_text=""), ("", "")
        )
        l1, l2 = self.carrier._transaher_split_observations(
            fallback_text=(" word" * 20).strip()
        )
        self.assertTrue(l1 and l2)
        l1_ns, l2_ns = self.carrier._transaher_split_observations(
            fallback_text="X" * 90
        )
        self.assertEqual(len(l1_ns), 70)
        self.assertEqual(len(l2_ns), 20)

        # Zero-weight, zero-volume product on SO and standalone picking
        zero_prod = self.env["product.product"].create(
            {
                "name": "Zero Weight Item",
                "type": "consu",
                "weight": 0.0,
                "list_price": 5.0,
            }
        )
        so_form = Form(self.env["sale.order"].with_context(tracking_disable=True))
        so_form.partner_id = self.partner
        with so_form.order_line.new() as ln:
            ln.product_id = zero_prod
            ln.product_uom_qty = 2.0
            ln.price_unit = 5.0
        so_zero = so_form.save()
        self.assertEqual(so_zero._get_estimated_weight(), 0.0)
        so_zero.action_confirm()
        pick_zero = so_zero.picking_ids[0]
        pick_zero.carrier_id = self.carrier
        pick_zero.number_of_packages = 2
        gw, vol, pkgs = self.carrier._transaher_estimate_order_metrics(so_zero)
        self.assertEqual(pkgs, 2)
        self.assertGreater(gw, 0.0)
        self.assertGreater(vol, 0.0)

        # Standalone picking without sale_id (origin, HTML note, zero shipping_weight)
        pick_zero.write(
            {
                "sale_id": False,
                "origin": "MANUAL-001",
                "note": "<p>Deliver at gate B</p>",
            }
        )
        self.partner.transaher_delivery_notes = False
        gw2, vol2, pkgs2 = self.carrier._transaher_prepare_picking_metrics(pick_zero)
        datos_z = self.carrier._transaher_build_datos_entrada(
            pick_zero, gw2, vol2, pkgs2
        )
        self.assertIn("MANUAL-001", datos_z)
        self.assertIn("Deliver at gate B", datos_z)

        # Datosentrada validation errors: missing partner, missing street, invalid zip
        with self.assertRaises(UserError):
            pick_no_partner = self.env["stock.picking"].new({"name": "TMP/001"})
            self.carrier._transaher_build_datos_entrada(pick_no_partner, 1.0, 0.01, 1)
        incomplete_partner = self.env["res.partner"].create({"name": "Incomplete"})
        with self.assertRaises(UserError):
            self.carrier._transaher_build_datos_entrada(
                pick_zero, 1.0, 0.01, 1, consignee=incomplete_partner
            )
        bad_zip_p = self.env["res.partner"].create(
            {
                "name": "Invalid Zip",
                "street": "Main 1",
                "city": "London",
                "zip": "   ",
                "country_id": self.country_es.id,
            }
        )
        with self.assertRaises(UserError):
            self.carrier._transaher_build_datos_entrada(
                pick_zero, 1.0, 0.01, 1, consignee=bad_zip_p
            )

    @mute_logger("odoo.addons.delivery_transaher.models.delivery_carrier")
    @patch(POST_PATH)
    def test_16_picking_actions_onchange_tracking_links_and_local_modes(
        self, mock_post
    ):
        """Test picking onchange, tracking URLs, ZPL/local_qweb, and edge cases."""
        self.partner.write(
            {
                "transaher_postal_rep_code": "02",
                "transaher_delivery_notes": "Llamar antes de entregar",
            }
        )
        self.picking.write({"transaher_obs_1": False, "transaher_obs_2": False})
        self.picking._onchange_partner_transaher_defaults()
        self.assertEqual(self.picking.transaher_postal_rep_code, "02")
        self.assertIn("Llamar", self.picking.transaher_obs_1)

        # Tracking link templates & open action
        self.picking.write(
            {"carrier_tracking_ref": False, "transaher_cod_expedicion": False}
        )
        self.assertFalse(self.picking.transaher_tracking_url)
        with self.assertRaises(UserError):
            self.picking.action_open_transaher_tracking_url()

        self.carrier.transaher_tracking_url = "https://track.example/{tracking_ref}"
        self.picking.transaher_cod_expedicion = "12685535"
        self.picking._compute_transaher_tracking_url()
        self.assertEqual(
            self.picking.transaher_tracking_url, "https://track.example/12685535"
        )
        url_act = self.picking.action_open_transaher_tracking_url()
        self.assertEqual(url_act["type"], "ir.actions.act_url")

        self.carrier.transaher_tracking_url = (
            "https://track.example/<shipmenttrackingnumber>"
        )
        self.assertEqual(
            self.carrier.transaher_get_tracking_link(self.picking),
            "https://track.example/12685535",
        )

        # Non-transaher carrier check & rate error branches
        other_carrier = self.env["delivery.carrier"].create(
            {
                "name": "Other Fixed",
                "delivery_type": "fixed",
                "product_id": self.delivery_product.id,
            }
        )
        self.picking.carrier_id = other_carrier
        with self.assertRaises(UserError):
            self.picking.action_transaher_get_label()
        self.picking.carrier_id = self.carrier

        orig_zip = self.partner.zip
        self.partner.zip = False
        rate_no_zip = self.carrier.transaher_rate_shipment(self.sale_order)
        self.assertFalse(rate_no_zip["success"])
        with self.assertRaises(UserError):
            self.picking.action_transaher_calculate_rate()

        self.partner.zip = "08001"
        rate_no_rule = self.carrier.transaher_rate_shipment(self.sale_order)
        self.assertFalse(rate_no_rule["success"])
        with self.assertRaises(UserError):
            self.picking.action_transaher_calculate_rate()
        self.partner.zip = orig_zip

        # EUR currency direct match in transaher_rate_shipment
        eur = self.env.ref("base.EUR")
        self.sale_order.currency_id = eur
        self.assertTrue(
            self.carrier.transaher_rate_shipment(self.sale_order)["success"]
        )

        # ZPL attachment & empty bytes attachment
        self.assertFalse(
            self.carrier._transaher_attach_label_to_picking(self.picking, b"", "123")
        )
        zpl_att = self.carrier._transaher_attach_label_to_picking(
            self.picking, b"^XA^XZ", "123", extension="zpl"
        )
        self.assertEqual(zpl_att.mimetype, "text/plain")

        # local_qweb mode + return_label_on_delivery + inherited SO estimated cost
        self.sale_order.write(
            {
                "transaher_estimated_cost": 19.50,
                "transaher_rate_breakdown": "Inherited Breakdown",
            }
        )
        self.carrier.write(
            {
                "transaher_label_mode": "local_qweb",
                "return_label_on_delivery": True,
            }
        )
        mock_post.side_effect = [
            self._mock_soap_response(self._xml_alta_response(cod_exp="33344455")),
            self._mock_soap_response(self._xml_alta_response(cod_exp="33344456")),
        ]
        self.picking.send_to_shipper()
        self.assertAlmostEqual(self.picking.transaher_estimated_cost, 19.50, places=2)
        self.carrier.write(
            {
                "transaher_label_mode": "ws_with_fallback",
                "return_label_on_delivery": False,
            }
        )
        mock_post.side_effect = None

        # action_transaher_get_label success & fetch_labels without expedition code
        self.carrier.sudo().write(
            {
                "transaher_cached_token": "VALID-TOK",
                "transaher_token_valid_until": "2099-12-31 23:59:59",
            }
        )
        mock_post.return_value = self._mock_soap_response(
            self._xml_etiquetas_response()
        )
        self.assertTrue(self.picking.action_transaher_get_label())

        self.picking.write(
            {"carrier_tracking_ref": False, "transaher_cod_expedicion": False}
        )
        with self.assertRaises(UserError):
            self.carrier.transaher_fetch_labels(self.picking)

        # Return label ws_only error vs ws_with_fallback QWeb fallback
        err_lbl = self._mock_soap_response(
            self._xml_etiquetas_response(pdf_b64="", has_error="true", level_err=True)
        )
        self.carrier.transaher_label_mode = "ws_only"
        mock_post.side_effect = [
            self._mock_soap_response(self._xml_alta_response(cod_exp="888111")),
            err_lbl,
        ]
        with self.assertRaises(UserError):
            self.carrier.transaher_get_return_label(self.picking)

        self.carrier.transaher_label_mode = "ws_with_fallback"
        mock_post.side_effect = [
            self._mock_soap_response(self._xml_alta_response(cod_exp="888112")),
            err_lbl,
        ]
        self.carrier.transaher_get_return_label(self.picking)
        mock_post.side_effect = None

        # Tracking early returns & zero amounts audit
        self.assertIsNone(self.carrier.transaher_tracking_state_update(self.picking))
        self.picking.transaher_cod_expedicion = "12685535"
        empty_trk = """<?xml version="1.0" encoding="utf-8"?>
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
          <s:Body>
            <executeResponse xmlns="MWSBridge.wsinformaciontransporte_services">
              <InfoTransporteRsp xmlns:a="MWSBridge">
                <a:Mensajes><a:errCod>0</a:errCod><a:errDsc/></a:Mensajes>
                <a:Expediciones/>
              </InfoTransporteRsp>
            </executeResponse>
          </s:Body>
        </s:Envelope>"""
        mock_post.return_value = self._mock_soap_response(empty_trk)
        self.assertIsNone(self.carrier.transaher_tracking_state_update(self.picking))
        vals_audit = {}
        self.carrier._transaher_audit_tracking_amounts(self.picking, [], vals_audit)
        self.carrier._transaher_audit_tracking_amounts(
            self.picking, [{"importe_neto": 0.0}], vals_audit
        )
        self.assertEqual(vals_audit, {})

    @patch(POST_PATH)
    def test_17_manifest_wizard_local_fallback_print_and_report(self, mock_post):
        """Test Manifest wizard date validation, local pickings, fallback, and print."""
        now = fields.Datetime.now()
        wiz_Model = self.env["transaher.manifest.wizard"]

        # Invalid date range (date_from > date_to)
        wiz_bad = wiz_Model.create(
            {
                "carrier_id": self.carrier.id,
                "date_from": now + timedelta(days=1),
                "date_to": now,
                "source_mode": "local_pickings",
            }
        )
        with self.assertRaises(UserError):
            wiz_bad.action_generate_manifest_pdf()

        # Empty local pickings range raises UserError
        wiz_empty = wiz_Model.create(
            {
                "carrier_id": self.carrier.id,
                "date_from": now - timedelta(days=30),
                "date_to": now - timedelta(days=29),
                "source_mode": "local_pickings",
            }
        )
        with self.assertRaises(UserError):
            wiz_empty.action_generate_manifest_pdf()

        # Mark picking done within range and test local_pickings + ws_with_fallback
        self.picking.write(
            {
                "state": "done",
                "date_done": now,
                "carrier_tracking_ref": "12685535",
                "transaher_cod_expedicion": "12685535",
            }
        )
        wiz_local = wiz_Model.create(
            {
                "carrier_id": self.carrier.id,
                "date_from": now - timedelta(hours=1),
                "date_to": now + timedelta(hours=1),
                "source_mode": "local_pickings",
            }
        )
        wiz_local.action_generate_manifest_pdf()
        self.assertTrue(wiz_local.pdf_file)

        # Direct print action & report rendering without pre-populated data dict
        print_act = wiz_local.action_print_manifest()
        self.assertEqual(print_act["type"], "ir.actions.report")
        rep = self.env.ref("delivery_transaher.action_report_transaher_manifest")
        pdf_bytes, _ext = rep._render_qweb_pdf(
            rep.report_name, res_ids=wiz_local.ids, data={}
        )
        self.assertTrue(pdf_bytes)

        # ws_with_fallback when WS raises UserError -> falls back to local pickings
        wiz_fb = wiz_Model.create(
            {
                "carrier_id": self.carrier.id,
                "date_from": now - timedelta(hours=1),
                "date_to": now + timedelta(hours=1),
                "source_mode": "ws_with_fallback",
            }
        )
        mock_post.side_effect = requests.exceptions.ConnectionError("Offline")
        wiz_fb.action_generate_manifest_pdf()
        self.assertTrue(wiz_fb.pdf_file)
        mock_post.side_effect = None

        # ws_with_fallback when WS returns empty Expediciones -> falls back to local
        empty_mnf_inner = "<MT_Return><ErrCod>0</ErrCod><Expediciones/></MT_Return>"
        empty_mnf_soap = (
            '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">'
            '<SOAP-ENV:Body><wsMnfPrtSOAP.ExecuteResponse xmlns="MTRANS_WEB">'
            f"<Respuesta>{escape(empty_mnf_inner)}</Respuesta>"
            "</wsMnfPrtSOAP.ExecuteResponse></SOAP-ENV:Body></SOAP-ENV:Envelope>"
        )
        mock_post.return_value = self._mock_soap_response(empty_mnf_soap)
        wiz_fb.action_generate_manifest_pdf()
        self.assertTrue(wiz_fb.pdf_file)
