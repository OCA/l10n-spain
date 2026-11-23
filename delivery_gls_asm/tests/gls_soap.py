# Copyright 2026 Studio73 - Pablo Cortés <pablo.cortes@studio73.es>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import binascii

LABEL_BYTES = b"%PDF-1.4 gls-label"
LABEL_B64 = binascii.b2a_base64(LABEL_BYTES).decode()
REQUEST_PATH = "odoo.addons.delivery_gls_asm.models.gls_asm_request"


class SoapNode:
    def __init__(self, **values) -> None:
        self.__keylist__ = list(values)
        for key, value in values.items():
            setattr(self, key, value)


class FakeGlsService:
    def __init__(self) -> None:
        self.calls = []
        self.cancel_return = "0"
        self.cancel_value = "Expedición anulada"
        self.cancel_error = False
        self.service_error = False
        self.shipment_return = "0"
        self.pickup_return = "0"
        self.with_label = True
        self.bad_references = False
        self.tracking_error = False
        self.tracking_exp = None
        self.pickup_clients = None
        self.label_error = False
        self.label_empty = False

    def GrabaServicios(self, docIn=None) -> SoapNode:
        xml = str(docIn)
        self.calls.append(("GrabaServicios", xml))
        if self.service_error:
            raise TimeoutError("GLS timeout")
        if "<Recogida " in xml:
            return SoapNode(
                Servicios=SoapNode(
                    Recogida=SoapNode(
                        _codigo="REC0000000000001",
                        Resultado=SoapNode(_return=self.pickup_return),
                    )
                )
            )
        references = "bad"
        if not self.bad_references:
            references = SoapNode(
                Referencia=[
                    SoapNode(_tipo="C", value="OTHER"),
                    SoapNode(_tipo="N", value="INT0000000000001"),
                    "plain",
                ]
            )
        shipment = {
            "_codexp": "EXP0000000000001",
            "_codbarras": "BAR0000000000001",
            "Resultado": SoapNode(_return=self.shipment_return),
            "Referencias": references,
        }
        if self.with_label:
            shipment["Etiquetas"] = SoapNode(Etiqueta=SoapNode(value=LABEL_B64))
        return SoapNode(Servicios=SoapNode(Envio=SoapNode(**shipment)))

    def GetExpCli(self, codigo=None, uid=None) -> SoapNode:
        self.calls.append(("GetExpCli", codigo))
        if self.tracking_error:
            raise TimeoutError("GLS timeout")
        exp = self.tracking_exp
        if exp is None:
            exp = {
                "codestado": "0",
                "estado": "MANIFESTADA",
                "tracking_list": {
                    "tracking": {
                        "fecha": "2026-01-01 10:00:00",
                        "codigo": "0",
                        "evento": "MANIFESTADA",
                    }
                },
            }
        return SoapNode(expediciones=SoapNode(exp=exp))

    def Tracking(self, docIn=None) -> SoapNode:
        self.calls.append(("Tracking", str(docIn)))
        clients = self.pickup_clients
        if clients is None:
            clients = SoapNode(
                Fecha="2026-01-01",
                Hora="10:00",
                Codigo="1",
                Descripcion="SOLICITADA",
            )
        return SoapNode(
            Servicios=SoapNode(
                Recogida=SoapNode(Tracking=SoapNode(TrackingCliente=clients))
            )
        )

    def Anula(self, docIn=None) -> SoapNode:
        self.calls.append(("Anula", str(docIn)))
        if self.cancel_error:
            raise TimeoutError("GLS timeout")
        xml = str(docIn)
        result = SoapNode(_return=self.cancel_return, value=self.cancel_value)
        if "<Recogida " in xml:
            return SoapNode(Servicios=SoapNode(Recogida=SoapNode(Resultado=result)))
        return SoapNode(Servicios=SoapNode(Envio=SoapNode(Resultado=result)))

    def EtiquetaEnvio(self, reference, label_format) -> SoapNode:
        self.calls.append(("EtiquetaEnvio", reference, label_format))
        if self.label_error:
            raise TimeoutError("GLS timeout")
        if self.label_empty:
            return SoapNode(base64Binary=[])
        return SoapNode(base64Binary=[LABEL_B64])


class FakeGlsClient:
    service = FakeGlsService()

    def __init__(self, *args, **kwargs) -> None:
        self.service = FakeGlsClient.service


def asdict(suds_object) -> dict:
    if isinstance(suds_object, dict):
        return suds_object
    values = {}
    for key in suds_object.__keylist__:
        values[key] = getattr(suds_object, key)
    return values
