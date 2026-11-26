# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
import re
from datetime import timedelta

import requests
from lxml import etree

from odoo import _, fields
from odoo.exceptions import UserError

from .transaher_master_data import (
    NS_MTRANS_WEB,
    NS_MWSBRIDGE,
    NS_SOAPENV,
    NS_WSETIEXP,
    NS_WSGETTOKEN,
    NS_WSINFOTRN,
    SOAP_ACTION_ALTA,
    SOAP_ACTION_BAJA,
    SOAP_ACTION_ETIQUETAS,
    SOAP_ACTION_INFO_TRANSPORTE,
    SOAP_ACTION_MANIFIESTO,
    SOAP_ACTION_TOKEN,
    TRANSAHER_BAJA_ERROR_MAP,
    TRANSAHER_DEFAULT_HOLDING,
    TRANSAHER_DEFAULT_PROTOCOLO,
    TRANSAHER_DEFAULT_SECCION,
    TRANSAHER_PROD_MBRIDGE_URL,
    TRANSAHER_PROD_MCLIENT_URL,
    TRANSAHER_TEST_MBRIDGE_URL,
    TRANSAHER_TEST_MCLIENT_URL,
    TRANSAHER_TOKEN_ERROR_MAP,
    TRANSAHER_TOKEN_TTL_MINUTES,
    normalize_soap_base_url,
)

_logger = logging.getLogger(__name__)


def _localname(tag):
    if not isinstance(tag, str):
        return ""
    if "}" in tag:
        return tag.split("}", 1)[1]
    if ":" in tag:
        return tag.split(":", 1)[1]
    return tag


def _find_first(elem, local_name):
    if elem is None:
        return None
    target = local_name.lower()
    for node in elem.iter():
        if node is not elem and _localname(node.tag).lower() == target:
            return node
    return None


def _find_direct(elem, local_name):
    if elem is None:
        return None
    target = local_name.lower()
    for child in elem:
        if _localname(child.tag).lower() == target:
            return child
    return None


def _find_all(elem, local_name):
    if elem is None:
        return []
    target = local_name.lower()
    return [
        node
        for node in elem.iter()
        if node is not elem and _localname(node.tag).lower() == target
    ]


def _child_text(elem, local_name, default=""):
    child = _find_direct(elem, local_name)
    if child is None:
        child = _find_first(elem, local_name)
    if child is None or child.text is None:
        return default
    return child.text.strip()


def _parse_spanish_float(val):
    if not val:
        return 0.0
    cleaned = str(val).strip()
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0


class TransaherRequest:
    """SOAP 1.1 client for all 6 Transaher Web Services (MClient & MBridge)."""

    def __init__(self, carrier):
        self.carrier = carrier
        self.env = carrier.env
        self.timeout = 30
        self._xml_parser = etree.XMLParser(
            resolve_entities=False,
            no_network=True,
            recover=True,
        )

    # -------------------------------------------------------------------------
    # Configuration & Credentials Helpers
    # -------------------------------------------------------------------------
    def _get_mclient_base_url(self):
        carrier = self.carrier.sudo()
        if carrier.prod_environment:
            return normalize_soap_base_url(
                carrier.transaher_prod_mclient_url, TRANSAHER_PROD_MCLIENT_URL
            )
        return normalize_soap_base_url(
            carrier.transaher_test_mclient_url, TRANSAHER_TEST_MCLIENT_URL
        )

    def _get_mbridge_base_url(self):
        carrier = self.carrier.sudo()
        if carrier.prod_environment:
            return normalize_soap_base_url(
                carrier.transaher_prod_mbridge_url, TRANSAHER_PROD_MBRIDGE_URL
            )
        return normalize_soap_base_url(
            carrier.transaher_test_mbridge_url, TRANSAHER_TEST_MBRIDGE_URL
        )

    def _get_credentials(self):
        carrier = self.carrier.sudo()
        if carrier.prod_environment:
            client_code = (
                carrier.transaher_client_code_prod or carrier.transaher_client_code_test
            )
            password = (
                carrier.transaher_password_prod or carrier.transaher_password_test
            )
        else:
            client_code = (
                carrier.transaher_client_code_test or carrier.transaher_client_code_prod
            )
            password = (
                carrier.transaher_password_test or carrier.transaher_password_prod
            )

        if not client_code or not password:
            env_name = _("Production") if carrier.prod_environment else _("Test")
            raise UserError(
                _(
                    "Missing Transaher Client Code or Password for %(env)s environment "
                    "on delivery method '%(carrier)s'."
                )
                % {"env": env_name, "carrier": self.carrier.name}
            )
        clean_code = str(client_code).strip()
        if not clean_code.isdigit():
            raise UserError(
                _("Transaher Client Code ('%s') must be numeric.") % clean_code
            )
        return int(clean_code), str(password).strip()

    @staticmethod
    def _mask_xml_for_logging(xml_str):
        if not xml_str:
            return ""
        masked = re.sub(
            r"(<(?:\w+:)?(?:PasswordCliente|Clipsw|Token)>)(.*?)(</(?:\w+:)?(?:PasswordCliente|Clipsw|Token)>)",
            r"\1***\3",
            xml_str,
            flags=re.DOTALL | re.IGNORECASE,
        )
        masked = re.sub(
            r"(<(?:\w+:)?Data>)([^<]{200,})(</(?:\w+:)?Data>)",
            lambda m: (
                f"{m.group(1)}<Base64 Data ({len(m.group(2))} chars)>{m.group(3)}"
            ),
            masked,
            flags=re.DOTALL,
        )
        return masked

    def _parse_xml_bytes(self, raw_bytes_or_str):
        if isinstance(raw_bytes_or_str, str):
            data = raw_bytes_or_str.encode("utf-8")
        else:
            data = raw_bytes_or_str
        return etree.fromstring(data, parser=self._xml_parser)

    def _post_soap(self, url, soap_action, envelope_elem, service_tag):
        xml_bytes = etree.tostring(
            envelope_elem,
            encoding="utf-8",
            xml_declaration=True,
        )
        xml_str = xml_bytes.decode("utf-8")
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": f'"{soap_action}"',
            "Accept": "text/xml, application/soap+xml, */*",
        }

        masked_req = self._mask_xml_for_logging(xml_str)
        self.carrier.log_xml(
            f'POST {url}\nSOAPAction: "{soap_action}"\n{masked_req}',
            f"transaher_request_{service_tag}",
        )

        try:
            response = requests.post(
                url,
                data=xml_bytes,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.exceptions.RequestException as exc:
            self.carrier.log_xml(str(exc), f"transaher_error_{service_tag}")
            raise UserError(
                _("Connection error with Transaher Web Service (%(url)s): %(err)s")
                % {"url": url, "err": exc}
            ) from exc

        resp_text = response.text or ""
        self.carrier.log_xml(
            f"HTTP {response.status_code}\n{self._mask_xml_for_logging(resp_text)}",
            f"transaher_response_{service_tag}",
        )

        root = None
        if response.content:
            try:
                root = self._parse_xml_bytes(response.content)
            except Exception as parse_exc:
                _logger.warning(
                    "Failed to parse Transaher XML from %s: %s", url, parse_exc
                )

        # Check for SOAP Fault first (often returned with HTTP 500)
        if root is not None:
            fault = _find_first(root, "Fault")
            if fault is not None:
                fault_code = _child_text(fault, "faultcode")
                fault_string = _child_text(fault, "faultstring") or _child_text(
                    fault, "Text"
                )
                raise UserError(
                    _("Transaher SOAP Fault [%(code)s] on %(svc)s:\n%(msg)s")
                    % {
                        "code": fault_code or response.status_code,
                        "svc": service_tag,
                        "msg": fault_string or resp_text[:400],
                    }
                )

        if response.status_code >= 400:
            raise UserError(
                _("Transaher HTTP %(code)s error on %(svc)s:\n%(body)s")
                % {
                    "code": response.status_code,
                    "svc": service_tag,
                    "body": resp_text[:500] or getattr(response, "reason", ""),
                }
            )

        if root is None:
            raise UserError(
                _(
                    "Transaher Web Service (%s) returned an empty or invalid "
                    "XML response."
                )
                % service_tag
            )
        return root

    # -------------------------------------------------------------------------
    # 1. Security Token Authentication (wsgetToken.svc - Section 2)
    # -------------------------------------------------------------------------
    def get_token(self, force_refresh=False):
        """Obtain or reuse a valid 20-minute security token via `wsgetToken`."""
        carrier = self.carrier.sudo()
        now = fields.Datetime.now()
        if (
            not force_refresh
            and carrier.transaher_cached_token
            and carrier.transaher_token_valid_until
            and carrier.transaher_token_valid_until > now
        ):
            return carrier.transaher_cached_token

        client_code, password = self._get_credentials()
        holding = (
            carrier.transaher_holding
            if carrier.transaher_holding is not False
            and carrier.transaher_holding is not None
            else TRANSAHER_DEFAULT_HOLDING
        )
        url = f"{self._get_mbridge_base_url()}/wsgetToken.svc"

        nsmap = {"soapenv": NS_SOAPENV, "mws": NS_WSGETTOKEN}
        envelope = etree.Element(f"{{{NS_SOAPENV}}}Envelope", nsmap=nsmap)
        etree.SubElement(envelope, f"{{{NS_SOAPENV}}}Header")
        body = etree.SubElement(envelope, f"{{{NS_SOAPENV}}}Body")
        execute = etree.SubElement(body, f"{{{NS_WSGETTOKEN}}}execute")
        etree.SubElement(execute, f"{{{NS_WSGETTOKEN}}}CodigoHolding").text = str(
            int(holding)
        )
        etree.SubElement(execute, f"{{{NS_WSGETTOKEN}}}CodigoCliente").text = str(
            client_code
        )
        etree.SubElement(execute, f"{{{NS_WSGETTOKEN}}}PasswordCliente").text = password

        root = self._post_soap(url, SOAP_ACTION_TOKEN, envelope, "wsgetToken")
        _resp = _find_first(root, "Response")
        resp_node = _resp if _resp is not None else root
        err_code_str = _child_text(resp_node, "errCode", "0")
        err_desc = _child_text(resp_node, "errDesc")
        token = _child_text(resp_node, "Token")

        try:
            err_code = int(err_code_str or 0)
        except ValueError:
            err_code = -1

        if err_code != 0 or not token:
            mapped_desc = TRANSAHER_TOKEN_ERROR_MAP.get(err_code, "")
            detail = err_desc or mapped_desc or _("No token returned by wsgetToken.")
            raise UserError(
                _("Transaher Authentication Error (code %(code)s): %(detail)s")
                % {"code": err_code, "detail": detail}
            )

        valid_until = now + timedelta(minutes=TRANSAHER_TOKEN_TTL_MINUTES)
        carrier.write(
            {
                "transaher_cached_token": token,
                "transaher_token_valid_until": valid_until,
            }
        )
        return token

    def _execute_with_token_retry(self, callback):
        """Execute a token-protected WCF call (`wsEtiExpSOAP` / tracking),
        renewing the token once if Transaher reports code 1/2 (expired token).
        """
        token = self.get_token(force_refresh=False)
        res = callback(token)
        if res.get("_token_expired"):
            _logger.info(
                "Transaher token expired; requesting a fresh token and retrying..."
            )
            token = self.get_token(force_refresh=True)
            res = callback(token)
            if res.get("_token_expired"):
                raise UserError(
                    _("Transaher rejected the newly generated security token: %s")
                    % (res.get("_token_error_msg") or _("Invalid or expired token"))
                )
        return res

    # -------------------------------------------------------------------------
    # 2. Create Expedition / Alta de Expedición (awsprcsatsoap.aspx - Section 3)
    # -------------------------------------------------------------------------
    def _parse_expedicion_xml_node(self, exp_node):
        """Parse an `<Expedicion>` element from `MT_Return` (Alta or Manifiesto)."""
        holding = _child_text(exp_node, "Holding")
        seccion = _child_text(exp_node, "Seccion")
        centro = _child_text(exp_node, "Centro")
        cod_exp = _child_text(exp_node, "CodExpedicion") or _child_text(
            exp_node, "NroExpedicion"
        )
        key_parts = [p for p in (holding, seccion, centro, cod_exp) if p != ""]
        return {
            "holding": int(holding) if holding.isdigit() else TRANSAHER_DEFAULT_HOLDING,
            "seccion": int(seccion) if seccion.isdigit() else TRANSAHER_DEFAULT_SECCION,
            "centro": int(centro) if centro.isdigit() else 0,
            "cod_expedicion": cod_exp,
            "expedition_key": ".".join(key_parts) if len(key_parts) == 4 else cod_exp,
            "fecha_expedicion": _child_text(exp_node, "Fecha_Expedicion"),
            "albaran_ordenante": _child_text(exp_node, "Albaran_Ordenante"),
            "mercancia": _child_text(exp_node, "Mercancia"),
            "descripcion_mercancia": _child_text(exp_node, "Descripcion_Mercancia"),
            "incoterm": _child_text(exp_node, "Incoterm"),
            "servicio": _child_text(exp_node, "Servicio"),
            "codigo_destinatario": _child_text(exp_node, "Codigo_Destinatario"),
            "nombre_destinatario": _child_text(exp_node, "Nombre_Destinatario"),
            "domicilio_destinatario": _child_text(exp_node, "Domicilio_Destinatario"),
            "postal_destinatario": _child_text(exp_node, "Postal_Destinatario"),
            "poblacion_destinatario": _child_text(exp_node, "Poblacion_Destinatario"),
            "provincia_destinatario": _child_text(exp_node, "Provincia_Destinatario"),
            "pais_destinatario": _child_text(exp_node, "Pais_Destinatario"),
            "nombre_remitente": _child_text(exp_node, "Nombre_Remitente"),
            "domicilio_remitente": _child_text(exp_node, "Domicilio_Remitente"),
            "postal_remitente": _child_text(exp_node, "Postal_Remitente"),
            "poblacion_remitente": _child_text(exp_node, "Poblacion_Remitente"),
            "pais_remitente": _child_text(exp_node, "Pais_Remitente"),
            "bultos": int(
                _parse_spanish_float(
                    _child_text(exp_node, "Total_Bultos")
                    or _child_text(exp_node, "Bultos")
                    or "0"
                )
            ),
            "peso": _parse_spanish_float(_child_text(exp_node, "Peso")),
            "volumen": _parse_spanish_float(_child_text(exp_node, "Volumen")),
            "observaciones": _child_text(exp_node, "Observaciones"),
            "area_dis_cod": _child_text(exp_node, "Area_Dis_Cod"),
            "area_dis_dsc": _child_text(exp_node, "Area_Dis_Dsc"),
            "nombre_ordenante": _child_text(exp_node, "Nombre_Ordenante"),
            "centro_destino": _child_text(exp_node, "Centro_Destino"),
            "expedicion_ch": _child_text(exp_node, "Expedicion_Ch"),
        }

    def create_expedition(self, datos_entrada, protocolo=None):
        """Call `awsprcsatsoap` (`wsPrcSATSOAP.Execute`) to register a shipment."""
        client_code, password = self._get_credentials()
        proto = int(
            protocolo or self.carrier.transaher_protocolo or TRANSAHER_DEFAULT_PROTOCOLO
        )
        url = f"{self._get_mclient_base_url()}/awsprcsatsoap.aspx"

        nsmap = {"soapenv": NS_SOAPENV, "mtr": NS_MTRANS_WEB}
        envelope = etree.Element(f"{{{NS_SOAPENV}}}Envelope", nsmap=nsmap)
        etree.SubElement(envelope, f"{{{NS_SOAPENV}}}Header")
        body = etree.SubElement(envelope, f"{{{NS_SOAPENV}}}Body")
        exec_el = etree.SubElement(body, f"{{{NS_MTRANS_WEB}}}wsPrcSATSOAP.Execute")
        etree.SubElement(exec_el, f"{{{NS_MTRANS_WEB}}}Clicod").text = str(client_code)
        etree.SubElement(exec_el, f"{{{NS_MTRANS_WEB}}}Clipsw").text = password
        etree.SubElement(exec_el, f"{{{NS_MTRANS_WEB}}}Ediprocod").text = str(proto)
        etree.SubElement(
            exec_el, f"{{{NS_MTRANS_WEB}}}Datosentrada"
        ).text = datos_entrada

        root = self._post_soap(url, SOAP_ACTION_ALTA, envelope, "awsprcsatsoap")
        respuesta_node = _find_first(root, "Respuesta")
        mt_return = None
        if (
            respuesta_node is not None
            and respuesta_node.text
            and respuesta_node.text.strip()
        ):
            raw_inner = respuesta_node.text.strip()
            self.carrier.log_xml(raw_inner, "transaher_parsed_awsprcsatsoap")
            mt_return = self._parse_xml_bytes(raw_inner)
        else:
            mt_return = _find_first(root, "MT_Return")

        if mt_return is None:
            raise UserError(
                _(
                    "Transaher Alta (`awsprcsatsoap`) did not return a valid "
                    "`<MT_Return>` XML payload."
                )
            )

        err_cod_str = _child_text(mt_return, "ErrCod", "0")
        err_dsc = _child_text(mt_return, "ErrDsc")
        try:
            err_cod = int(err_cod_str or 0)
        except ValueError:
            err_cod = -1

        if err_cod != 0:
            raise UserError(
                _("Transaher Expedition Creation Error (ErrCod %(code)s): %(desc)s")
                % {
                    "code": err_cod_str,
                    "desc": err_dsc or _("Unknown error in awsprcsatsoap"),
                }
            )

        exp_nodes = _find_all(mt_return, "Expedicion")
        if not exp_nodes:
            raise UserError(
                _(
                    "Transaher Alta returned ErrCod=0 but no `<Expedicion>` "
                    "element was included."
                )
            )
        parsed = self._parse_expedicion_xml_node(exp_nodes[0])
        if not parsed.get("cod_expedicion"):
            raise UserError(
                _("Transaher Alta did not return an expedition code (`CodExpedicion`).")
            )
        return parsed

    # -------------------------------------------------------------------------
    # 3. Cancel Expedition / Baja de Expedición (awsexpbaja.aspx - Section 4)
    # -------------------------------------------------------------------------
    def cancel_expedition(self, holcod, seccod, expctrcod, expcod):
        """Call `awsExpBaja` (`wsExpBaja.Execute`) to cancel an expedition."""
        client_code, password = self._get_credentials()
        expcod_digits = re.sub(r"\D", "", str(expcod or ""))
        if not expcod_digits:
            raise UserError(
                _("Invalid Transaher expedition number ('%s') for cancellation.")
                % expcod
            )

        url = f"{self._get_mclient_base_url()}/awsexpbaja.aspx"
        nsmap = {"soapenv": NS_SOAPENV, "mtr": NS_MTRANS_WEB}
        envelope = etree.Element(f"{{{NS_SOAPENV}}}Envelope", nsmap=nsmap)
        etree.SubElement(envelope, f"{{{NS_SOAPENV}}}Header")
        body = etree.SubElement(envelope, f"{{{NS_SOAPENV}}}Body")
        exec_el = etree.SubElement(body, f"{{{NS_MTRANS_WEB}}}wsExpBaja.Execute")
        etree.SubElement(exec_el, f"{{{NS_MTRANS_WEB}}}Clicod").text = str(client_code)
        etree.SubElement(exec_el, f"{{{NS_MTRANS_WEB}}}Clipsw").text = password
        etree.SubElement(exec_el, f"{{{NS_MTRANS_WEB}}}Holcod").text = str(
            int(holcod or 0)
        )
        etree.SubElement(exec_el, f"{{{NS_MTRANS_WEB}}}Seccod").text = str(
            int(seccod or 10)
        )
        etree.SubElement(exec_el, f"{{{NS_MTRANS_WEB}}}Expctrcod").text = str(
            int(expctrcod or 0)
        )
        etree.SubElement(exec_el, f"{{{NS_MTRANS_WEB}}}Expcod").text = str(
            int(expcod_digits)
        )

        root = self._post_soap(url, SOAP_ACTION_BAJA, envelope, "awsexpbaja")
        _resp = _find_first(root, "wsExpBaja.ExecuteResponse")
        resp_node = _resp if _resp is not None else root
        err_cod_str = _child_text(resp_node, "Errcod", "0")
        err_desc = _child_text(resp_node, "Errdesc")

        try:
            err_cod = int(err_cod_str or 0)
        except ValueError:
            err_cod = -1

        if err_cod != 0:
            reason = TRANSAHER_BAJA_ERROR_MAP.get(
                err_cod, _("Cancellation rejected by Transaher")
            )
            if err_desc and err_desc.lower() not in reason.lower():
                reason = f"{reason} ({err_desc})"
            raise UserError(
                _("Transaher Expedition Cancellation Error (code %(code)s): %(reason)s")
                % {"code": err_cod, "reason": reason}
            )
        return {"err_cod": 0, "err_desc": err_desc or "OK"}

    # -------------------------------------------------------------------------
    # 4. Print Expedition Labels (wsetiexpsoap.svc - Section 6)
    # -------------------------------------------------------------------------
    @staticmethod
    def _parse_labels_response_node(resp_node):
        """Parse `<Response>` element from `wsEtiExpSOAP`."""
        if resp_node is None:
            return False, "", [], []
        global_key = _child_text(resp_node, "Key")
        has_error = _child_text(resp_node, "HasError").lower() == "true"
        messages = []
        levels = []

        msgs_container = _find_direct(resp_node, "Messages")
        if msgs_container is not None:
            for msg_item in _find_all(msgs_container, "TW_wsEtiExpSOAP_Response.Item"):
                messages.append(
                    {
                        "id": _child_text(msg_item, "Id"),
                        "type": _child_text(msg_item, "Type"),
                        "description": _child_text(msg_item, "Description"),
                    }
                )

        levels_container = _find_direct(resp_node, "Levels")
        if levels_container is not None:
            for lvl in _find_all(levels_container, "TW_wsEtiExpSOAP_Response"):
                lvl_msgs = []
                lvl_msgs_container = _find_direct(lvl, "Messages")
                if lvl_msgs_container is not None:
                    for m_it in _find_all(
                        lvl_msgs_container, "TW_wsEtiExpSOAP_Response.Item"
                    ):
                        lvl_msgs.append(
                            {
                                "id": _child_text(m_it, "Id"),
                                "type": _child_text(m_it, "Type"),
                                "description": _child_text(m_it, "Description"),
                            }
                        )
                levels.append(
                    {
                        "name": _child_text(lvl, "Name"),
                        "key": _child_text(lvl, "Key"),
                        "has_error": _child_text(lvl, "HasError").lower() == "true",
                        "messages": lvl_msgs,
                    }
                )
        return has_error, global_key, messages, levels

    def get_labels(self, expeditions, posicion_inicial=""):
        """Download Base64 PDF/ZPL labels for expeditions via `wsEtiExpSOAP`.
        `expeditions`: list of dicts with `holding`, `seccion`, `centro`,
        `codigo`, and `bultos`.
        """
        if not expeditions:
            raise UserError(
                _("At least one Transaher expedition is required to request labels.")
            )

        url = f"{self._get_mbridge_base_url()}/wsetiexpsoap.svc"

        def _do_call(token):
            nsmap = {
                "soapenv": NS_SOAPENV,
                "mws": NS_WSETIEXP,
                "mws1": NS_MWSBRIDGE,
            }
            envelope = etree.Element(f"{{{NS_SOAPENV}}}Envelope", nsmap=nsmap)
            etree.SubElement(envelope, f"{{{NS_SOAPENV}}}Header")
            body = etree.SubElement(envelope, f"{{{NS_SOAPENV}}}Body")
            execute = etree.SubElement(body, f"{{{NS_WSETIEXP}}}execute")
            etree.SubElement(execute, f"{{{NS_WSETIEXP}}}Token").text = token

            params_el = etree.SubElement(execute, f"{{{NS_WSETIEXP}}}wsEtiExpParams")
            if posicion_inicial:
                etree.SubElement(
                    params_el, f"{{{NS_MWSBRIDGE}}}PosicionInicialImpresion"
                ).text = str(posicion_inicial).strip()
            exps_container = etree.SubElement(
                params_el, f"{{{NS_MWSBRIDGE}}}Expediciones"
            )

            for exp in expeditions:
                item_el = etree.SubElement(
                    exps_container,
                    f"{{{NS_MWSBRIDGE}}}wsEtiExpSOAPParams.Expedicion",
                )
                etree.SubElement(item_el, f"{{{NS_MWSBRIDGE}}}Holding").text = str(
                    int(exp.get("holding", TRANSAHER_DEFAULT_HOLDING))
                )
                etree.SubElement(item_el, f"{{{NS_MWSBRIDGE}}}Seccion").text = str(
                    int(exp.get("seccion", TRANSAHER_DEFAULT_SECCION))
                )
                etree.SubElement(item_el, f"{{{NS_MWSBRIDGE}}}Centro").text = str(
                    int(exp.get("centro", 0))
                )
                etree.SubElement(item_el, f"{{{NS_MWSBRIDGE}}}Codigo").text = str(
                    exp.get("codigo") or ""
                ).strip()
                bultos_el = etree.SubElement(item_el, f"{{{NS_MWSBRIDGE}}}Bultos")
                bultos_val = exp.get("bultos")
                bultos_el.text = "" if bultos_val is None else str(bultos_val)

            root = self._post_soap(url, SOAP_ACTION_ETIQUETAS, envelope, "wsetiexpsoap")
            file_node = _find_first(root, "FileBase64String")
            resp_node = _find_first(root, "Response")

            file_data = {
                "name": _child_text(file_node, "Name", "Transaher_Label"),
                "extension": (_child_text(file_node, "Extension", "pdf") or "pdf")
                .lower()
                .lstrip("."),
                "content_type": _child_text(
                    file_node, "ContentType", "application/pdf"
                ),
                "data": _child_text(file_node, "Data"),
            }

            has_error, global_key, messages, levels = self._parse_labels_response_node(
                resp_node
            )

            # Check if failure is due to expired/invalid security token (codes 1 or 2)
            all_msgs_text = " ".join(
                f"{m['id']} {m['description']}"
                for m in (messages + [lm for lv in levels for lm in lv["messages"]])
            ).lower()
            if (has_error or not file_data["data"]) and (
                global_key in ("1", "2")
                or "token" in all_msgs_text
                or "caducad" in all_msgs_text
            ):
                return {
                    "_token_expired": True,
                    "_token_error_msg": all_msgs_text or global_key,
                }

            return {
                **file_data,
                "has_error": has_error,
                "key": global_key,
                "messages": messages,
                "levels": levels,
            }

        result = self._execute_with_token_retry(_do_call)

        # Collect errors from global Messages and per-expedition Levels (Section 6.4)
        error_lines = []
        for msg in result.get("messages") or []:
            if (msg.get("type") or "").upper() == "ERROR" or result.get("has_error"):
                error_lines.append(
                    f"[{msg.get('id') or 'ERROR'}] {msg.get('description')}"
                )
        for lvl in result.get("levels") or []:
            if lvl.get("has_error"):
                for msg in lvl.get("messages") or []:
                    err_id = msg.get("id") or "ERROR"
                    error_lines.append(
                        f"Expedition {lvl.get('key')}: [{err_id}] "
                        f"{msg.get('description')}"
                    )

        if not result.get("data"):
            detail = "\n".join(error_lines) or _(
                "No Base64 PDF/ZPL data returned by wsEtiExpSOAP."
            )
            raise UserError(_("Transaher Label Error (`wsEtiExpSOAP`):\n%s") % detail)

        return result

    # -------------------------------------------------------------------------
    # 5. Shipment Status & Tracking (wsInformacionTransporte.svc - Section 7)
    # -------------------------------------------------------------------------
    def get_tracking_info(
        self,
        holding=None,
        seccion=None,
        centro=None,
        numero_expedicion=None,
        albaran_ordenante=None,
        fecha_desde=None,
        fecha_hasta=None,
        include_events=True,
        include_incidences=True,
        include_packages=True,
        include_amounts=True,
    ):
        """Query shipment status, events, incidences, packages, and freight costs
        via `wsInformacionTransporte.svc` (following WCF `InfoTransporteFiltros`).
        """
        url = f"{self._get_mbridge_base_url()}/wsInformacionTransporte.svc"

        def _do_call(token):
            nsmap = {
                "soapenv": NS_SOAPENV,
                "mws": NS_WSINFOTRN,
                "mws1": NS_MWSBRIDGE,
            }
            envelope = etree.Element(f"{{{NS_SOAPENV}}}Envelope", nsmap=nsmap)
            etree.SubElement(envelope, f"{{{NS_SOAPENV}}}Header")
            body = etree.SubElement(envelope, f"{{{NS_SOAPENV}}}Body")
            execute = etree.SubElement(body, f"{{{NS_WSINFOTRN}}}execute")
            etree.SubElement(execute, f"{{{NS_WSINFOTRN}}}Token").text = token

            filtros = etree.SubElement(execute, f"{{{NS_WSINFOTRN}}}InfoTrnFiltros")
            etree.SubElement(filtros, f"{{{NS_MWSBRIDGE}}}Info_Exp").text = "S"
            etree.SubElement(filtros, f"{{{NS_MWSBRIDGE}}}Info_Ent").text = "S"
            etree.SubElement(filtros, f"{{{NS_MWSBRIDGE}}}Info_Blt").text = (
                "S" if include_packages else "N"
            )
            etree.SubElement(filtros, f"{{{NS_MWSBRIDGE}}}Info_Exp_Inc").text = (
                "S" if include_incidences else "N"
            )
            etree.SubElement(filtros, f"{{{NS_MWSBRIDGE}}}Info_Exp_Evt").text = (
                "S" if include_events else "N"
            )
            etree.SubElement(filtros, f"{{{NS_MWSBRIDGE}}}Info_Ent_Inc").text = (
                "S" if include_incidences else "N"
            )
            etree.SubElement(filtros, f"{{{NS_MWSBRIDGE}}}Info_Ent_Evt").text = (
                "S" if include_events else "N"
            )
            etree.SubElement(filtros, f"{{{NS_MWSBRIDGE}}}Info_Importes").text = (
                "S" if include_amounts else "N"
            )

            # Strict XSD sequence order for WCF DataContractSerializer:
            # Holding -> Seccion -> Empresa -> Centro -> NumeroExpedicion ->
            # Fecha_Desde -> Fecha_Hasta -> Albaran_Ordenante
            if holding is not None and holding is not False:
                etree.SubElement(filtros, f"{{{NS_MWSBRIDGE}}}Holding").text = str(
                    int(holding)
                )
            if seccion is not None and seccion is not False:
                etree.SubElement(filtros, f"{{{NS_MWSBRIDGE}}}Seccion").text = str(
                    int(seccion)
                )
            if centro is not None and centro is not False and int(centro) > 0:
                etree.SubElement(filtros, f"{{{NS_MWSBRIDGE}}}Centro").text = str(
                    int(centro)
                )
            if numero_expedicion:
                etree.SubElement(
                    filtros, f"{{{NS_MWSBRIDGE}}}NumeroExpedicion"
                ).text = str(numero_expedicion).strip()
            if fecha_desde:
                etree.SubElement(filtros, f"{{{NS_MWSBRIDGE}}}Fecha_Desde").text = str(
                    fecha_desde
                )
            if fecha_hasta:
                etree.SubElement(filtros, f"{{{NS_MWSBRIDGE}}}Fecha_Hasta").text = str(
                    fecha_hasta
                )
            if albaran_ordenante:
                etree.SubElement(
                    filtros, f"{{{NS_MWSBRIDGE}}}Albaran_Ordenante"
                ).text = str(albaran_ordenante).strip()

            root = self._post_soap(
                url, SOAP_ACTION_INFO_TRANSPORTE, envelope, "wsInformacionTransporte"
            )
            _rsp = _find_first(root, "InfoTransporteRsp")
            rsp_node = _rsp if _rsp is not None else root
            _msg = _find_direct(rsp_node, "Mensajes")
            mensajes_node = (
                _msg if _msg is not None else _find_first(rsp_node, "Mensajes")
            )

            err_cod = 0
            err_dsc = ""
            if mensajes_node is not None:
                err_cod_raw = _child_text(mensajes_node, "errCod", "0")
                err_dsc = _child_text(mensajes_node, "errDsc")
                try:
                    err_cod = int(err_cod_raw or 0)
                except ValueError:
                    err_cod = -1

            if (
                err_cod in (1, 2)
                or "token" in err_dsc.lower()
                or "caducad" in err_dsc.lower()
            ):
                return {
                    "_token_expired": True,
                    "_token_error_msg": err_dsc or str(err_cod),
                }

            if err_cod != 0:
                raise UserError(
                    _(
                        "Transaher Tracking Error (`wsInformacionTransporte` "
                        "code %(code)s): %(desc)s"
                    )
                    % {
                        "code": err_cod,
                        "desc": err_dsc or _("Error querying transport info"),
                    }
                )

            expediciones = []
            exps_container = _find_direct(rsp_node, "Expediciones")
            if exps_container is not None:
                for sdt_exp in _find_all(exps_container, "sdtExpedicion"):
                    expediciones.append(self._parse_sdt_expedicion(sdt_exp))

            return {
                "err_cod": err_cod,
                "err_dsc": err_dsc,
                "expediciones": expediciones,
            }

        return self._execute_with_token_retry(_do_call)

    def _parse_sdt_expedicion(self, sdt_exp):
        """Parse an `<sdtExpedicion>` element from `wsInformacionTransporte`."""
        events = []
        incidences = []
        packages = []
        deliveries = []
        amounts = []

        ev_container = _find_direct(sdt_exp, "Eventos")
        if ev_container is not None:
            for ev in _find_all(ev_container, "sdtEvento"):
                events.append(
                    {
                        "date": _child_text(ev, "FHRegistro"),
                        "situacion_cod": _child_text(ev, "SituacionCodigo"),
                        "situacion_dsc": _child_text(ev, "SituacionDescripcion"),
                        "tipo_cod": _child_text(ev, "TipoCodigo"),
                        "tipo_dsc": _child_text(ev, "TipoDescripcion"),
                        "causa_dsc": _child_text(ev, "CausaDescripcion"),
                        "desc_1": _child_text(ev, "DescripcionUno"),
                        "desc_2": _child_text(ev, "DescripcionDos"),
                    }
                )

        inc_container = _find_direct(sdt_exp, "Incidencias")
        if inc_container is not None:
            for inc in _find_all(inc_container, "sdtIncidencia"):
                incidences.append(
                    {
                        "date": _child_text(inc, "FechaRegistro"),
                        "situacion_cod": _child_text(inc, "SituacionCodigo"),
                        "situacion_dsc": _child_text(inc, "SituacionDescripcion"),
                        "tipo_dsc": _child_text(inc, "TipoDescripcion"),
                        "causa_dsc": _child_text(inc, "CausaDescripcion"),
                        "desc_1": _child_text(inc, "DescripcionUno"),
                        "desc_2": _child_text(inc, "DescripcionDos"),
                    }
                )

        ent_container = _find_direct(sdt_exp, "Entregas")
        if ent_container is not None:
            for ent in _find_all(ent_container, "sdtEntrega"):
                deliveries.append(
                    {
                        "situacion": _child_text(ent, "Situacion"),
                        "fh_alta": _child_text(ent, "FHAlta"),
                        "fh_asignacion": _child_text(ent, "FHAsignacion"),
                        "fh_servicio": _child_text(ent, "FHServicio"),
                        "centro_destino_dsc": _child_text(
                            ent, "CentroDestinoDescripcion"
                        ),
                    }
                )
                ent_ev_cont = _find_direct(ent, "Eventos")
                if ent_ev_cont is not None:
                    for ev in _find_all(ent_ev_cont, "sdtEvento"):
                        events.append(
                            {
                                "date": _child_text(ev, "FHRegistro"),
                                "situacion_cod": _child_text(ev, "SituacionCodigo"),
                                "situacion_dsc": _child_text(
                                    ev, "SituacionDescripcion"
                                ),
                                "tipo_cod": _child_text(ev, "TipoCodigo"),
                                "tipo_dsc": _child_text(ev, "TipoDescripcion"),
                                "causa_dsc": _child_text(ev, "CausaDescripcion"),
                                "desc_1": _child_text(ev, "DescripcionUno"),
                                "desc_2": _child_text(ev, "DescripcionDos"),
                            }
                        )
                ent_inc_cont = _find_direct(ent, "Incidencias")
                if ent_inc_cont is not None:
                    for inc in _find_all(ent_inc_cont, "sdtIncidencia"):
                        incidences.append(
                            {
                                "date": _child_text(inc, "FechaRegistro"),
                                "situacion_cod": _child_text(inc, "SituacionCodigo"),
                                "situacion_dsc": _child_text(
                                    inc, "SituacionDescripcion"
                                ),
                                "tipo_dsc": _child_text(inc, "TipoDescripcion"),
                                "causa_dsc": _child_text(inc, "CausaDescripcion"),
                                "desc_1": _child_text(inc, "DescripcionUno"),
                                "desc_2": _child_text(inc, "DescripcionDos"),
                            }
                        )

        blt_container = _find_direct(sdt_exp, "Bultos")
        if blt_container is not None:
            for blt in _find_all(blt_container, "sdtBulto"):
                packages.append(
                    {
                        "bulto_relativo": _child_text(blt, "BultoRelativo"),
                        "tipo_bulto": _child_text(blt, "TipoBulto"),
                        "ean": _child_text(blt, "EAN"),
                        "sscc": _child_text(blt, "SSCC"),
                        "peso": _parse_spanish_float(_child_text(blt, "Peso")),
                        "volumen": _parse_spanish_float(_child_text(blt, "Volumen")),
                    }
                )

        imp_container = _find_direct(sdt_exp, "Importes")
        if imp_container is not None:
            for imp in _find_all(imp_container, "sdtImportes"):
                amounts.append(
                    {
                        "concepto_cod": _child_text(imp, "ConceptoCod"),
                        "concepto_dsc": _child_text(imp, "ConceptoDsc"),
                        "baremo_dsc": _child_text(imp, "BaremoDsc"),
                        "divisa": _child_text(imp, "Divisa") or "EUR",
                        "importe_neto": _parse_spanish_float(
                            _child_text(imp, "ImporteNeto")
                        ),
                        "situacion": _child_text(imp, "Situacion"),
                        "factura_centro": _child_text(imp, "FacturaCentro"),
                        "factura_serie": _child_text(imp, "FacturaSerie"),
                        "factura_numero": _child_text(imp, "FacturaNumero"),
                    }
                )

        return {
            "holding": _child_text(sdt_exp, "Holding"),
            "seccion": _child_text(sdt_exp, "Seccion"),
            "centro": _child_text(sdt_exp, "Centro"),
            "nro_expedicion": _child_text(sdt_exp, "NroExpedicion"),
            "situacion": _child_text(sdt_exp, "Situacion"),
            "fh_uno": _child_text(sdt_exp, "FHUno"),
            "fh_dos": _child_text(sdt_exp, "FHDos"),
            "fh_tres": _child_text(sdt_exp, "FHTres"),
            "albaran_ordenante": _child_text(sdt_exp, "AlbaranOrdenante"),
            "albaran_remitente": _child_text(sdt_exp, "AlbaranRemitente"),
            "servicio_dsc": _child_text(sdt_exp, "ServicioDescripcion"),
            "centro_origen": _child_text(sdt_exp, "CentroOrigen"),
            "centro_destino": _child_text(sdt_exp, "CentroDestino"),
            "area_destino": _child_text(sdt_exp, "AreaDestino"),
            "area_dis_cod": _child_text(sdt_exp, "AreaDistribucionCodigo"),
            "area_dis_dsc": _child_text(sdt_exp, "AreaDistribucionDescripcion"),
            "chofer_dsc": _child_text(sdt_exp, "ChoferDescripcion"),
            "tracking_number": _child_text(sdt_exp, "TrackingNumber"),
            "su_factura": _child_text(sdt_exp, "SuFactura"),
            "events": events,
            "incidences": incidences,
            "deliveries": deliveries,
            "packages": packages,
            "amounts": amounts,
        }

    # -------------------------------------------------------------------------
    # 6. Daily Manifest / Manifiesto (awsmnfprtsoap.aspx - Section 8)
    # -------------------------------------------------------------------------
    def get_manifest_data(self, fch_desde, fch_hasta, protocolo=None):
        """Call `awsmnfprtsoap` (`wsMnfPrtSOAP.Execute`) with `aaaammddhhmm` range
        and return parsed expedition records to render the PDF Manifest.
        """
        client_code, password = self._get_credentials()
        proto = int(
            protocolo or self.carrier.transaher_protocolo or TRANSAHER_DEFAULT_PROTOCOLO
        )
        url = f"{self._get_mclient_base_url()}/awsmnfprtsoap.aspx"

        nsmap = {"soapenv": NS_SOAPENV, "mtr": NS_MTRANS_WEB}
        envelope = etree.Element(f"{{{NS_SOAPENV}}}Envelope", nsmap=nsmap)
        etree.SubElement(envelope, f"{{{NS_SOAPENV}}}Header")
        body = etree.SubElement(envelope, f"{{{NS_SOAPENV}}}Body")
        exec_el = etree.SubElement(body, f"{{{NS_MTRANS_WEB}}}wsMnfPrtSOAP.Execute")
        etree.SubElement(exec_el, f"{{{NS_MTRANS_WEB}}}Clicod").text = str(client_code)
        etree.SubElement(exec_el, f"{{{NS_MTRANS_WEB}}}Clipsw").text = password
        etree.SubElement(exec_el, f"{{{NS_MTRANS_WEB}}}Ediprocod").text = str(proto)
        etree.SubElement(exec_el, f"{{{NS_MTRANS_WEB}}}Fchdesde").text = str(
            fch_desde
        ).strip()
        etree.SubElement(exec_el, f"{{{NS_MTRANS_WEB}}}Fchhasta").text = str(
            fch_hasta
        ).strip()

        root = self._post_soap(url, SOAP_ACTION_MANIFIESTO, envelope, "awsmnfprtsoap")
        respuesta_node = _find_first(root, "Respuesta")

        inner_root = None
        if (
            respuesta_node is not None
            and respuesta_node.text
            and respuesta_node.text.strip()
        ):
            raw_inner = respuesta_node.text.strip()
            self.carrier.log_xml(raw_inner, "transaher_parsed_awsmnfprtsoap")
            inner_root = self._parse_xml_bytes(raw_inner)
        else:
            _mtr = _find_first(root, "MT_Return")
            inner_root = _mtr if _mtr is not None else root

        err_cod_str = _child_text(inner_root, "ErrCod", "0")
        err_dsc = _child_text(inner_root, "ErrDsc")
        try:
            err_cod = int(err_cod_str or 0)
        except ValueError:
            err_cod = -1

        if err_cod != 0:
            raise UserError(
                _(
                    "Transaher Manifest Error (`awsmnfprtsoap` ErrCod %(code)s): "
                    "%(desc)s"
                )
                % {
                    "code": err_cod_str,
                    "desc": err_dsc or _("Error retrieving manifest"),
                }
            )

        exp_nodes = _find_all(inner_root, "Expedicion")
        return [self._parse_expedicion_xml_node(node) for node in exp_nodes]
