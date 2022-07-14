# Copyright (2021) Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from enum import Enum

from lxml import etree

_logger = logging.getLogger(__name__)

try:
    import xmltodict
except (ImportError, IOError) as err:
    _logger.error(err)


class LROEOperationTypeEnum(Enum):
    alta_sg_invoice_pj_240 = "alta_sg_invoice_pj_240"
    alta_sg_invoice_pf_140 = "alta_sg_invoice_pf_140"
    cancel_sg_invoice_pj_240 = "cancel_sg_invoice_pj_240"
    cancel_sg_invoice_pf_140 = "cancel_sg_invoice_pf_140"
    resp_alta_sg_invoice_pj_240 = "resp_alta_sg_invoice_pj_240"
    resp_alta_sg_invoice_pf_140 = "resp_alta_sg_invoice_pf_140"
    resp_cancel_sg_invoice_pj_240 = "resp_cancel_sg_invoice_pj_240"
    resp_cancel_sg_invoice_pf_140 = "resp_cancel_sg_invoice_pf_140"
    alta_invoice_in_pj_240 = "alta_invoice_in_pj_240"
    cancel_invoice_in_pj_240 = "cancel_invoice_in_pj_240"
    resp_alta_invoice_in_pj_240 = "resp_alta_invoice_in_pj_240"
    resp_cancel_invoice_in_pj_240 = "resp_cancel_invoice_in_pj_240"
    alta_invoice_in_pf_140 = "alta_invoice_in_pf_140"
    cancel_invoice_in_pf_140 = "cancel_invoice_in_pf_140"
    resp_alta_invoice_in_pf_140 = "resp_alta_invoice_in_pf_140"
    resp_cancel_invoice_in_pf_140 = "resp_cancel_invoice_in_pf_140"


class LROEXMLSchemaException(Exception):
    def __init__(self, name, value=None):
        if type(self) == LROEXMLSchemaException:
            _logger.warning(
                "You should implement a non generic Exception for your particular use "
                "case."
            )
        self.name = name
        self.value = value
        self.args = (name, value)


class LROEXMLSchemaModeNotSupported(LROEXMLSchemaException):
    """Mode - Invoice file type not supported"""

    def __init__(self, msg):
        super(LROEXMLSchemaModeNotSupported, self).__init__(msg)


class LROEXMLSchema:
    version = "1.0.7"
    schemas_version_dirname = "v1.0.7"
    ns = "http://www.w3.org/2001/XMLSchema"
    default_min_occurs = 1
    tags_to_ignore = ["{%s}complexType" % ns, "{%s}sequence" % ns]
    choice_tag = "{%s}choice" % ns

    lroe_operation_data = {
        LROEOperationTypeEnum.alta_sg_invoice_pj_240.value: {
            "operation_ns": (
                "https://www.batuz.eus/fitxategiak/batuz/LROE/esquemas/"
                "LROE_PJ_240_1_1_FacturasEmitidas_ConSG_AltaPeticion_V1_0_2.xsd"
            ),
            "root_element": "LROEPJ240FacturasEmitidasConSGAltaPeticion",
            "operation_nsmap": "lrpjfecsgap",
        },
        LROEOperationTypeEnum.alta_sg_invoice_pf_140.value: {
            "operation_ns": (
                "https://www.batuz.eus/fitxategiak/batuz/LROE/esquemas/"
                "LROE_PF_140_1_1_Ingresos_ConfacturaConSG_AltaPeticion_V1_0_2.xsd"
            ),
            "root_element": "LROEPF140IngresosConFacturaConSGAltaPeticion",
            "operation_nsmap": "lrpjfecsgap",
        },
        LROEOperationTypeEnum.cancel_sg_invoice_pj_240.value: {
            "operation_ns": (
                "https://www.batuz.eus/fitxategiak/batuz/LROE/esquemas/"
                "LROE_PJ_240_1_1_FacturasEmitidas_ConSG_AnulacionPeticion_V1_0_0.xsd"
            ),
            "root_element": "LROEPJ240FacturasEmitidasConSGAnulacionPeticion",
            "operation_nsmap": "lrpjfecsgap",
        },
        LROEOperationTypeEnum.cancel_sg_invoice_pf_140.value: {
            "operation_ns": (
                "https://www.batuz.eus/fitxategiak/batuz/LROE/esquemas/"
                "LROE_PF_140_1_1_Ingresos_ConfacturaConSG_AnulacionPeticion_V1_0_0.xsd"
            ),
            "root_element": "LROEPF140IngresosConFacturaConSGAnulacionPeticion",
            "operation_nsmap": "lrpjfecsgap",
        },
        LROEOperationTypeEnum.resp_alta_sg_invoice_pj_240.value: {
            "operation_ns": (
                "https://www.batuz.eus/fitxategiak/batuz/LROE/esquemas/"
                "LROE_PJ_240_1_1_FacturasEmitidas_ConSG_AltaRespuesta_V1_0_1.xsd"
            ),
            "root_element": "LROEPJ240FacturasEmitidasConSGAltaRespuesta",
            "operation_nsmap": "lrpjfecsgap",
        },
        LROEOperationTypeEnum.resp_alta_sg_invoice_pf_140.value: {
            "operation_ns": (
                "https://www.batuz.eus/fitxategiak/batuz/LROE/esquemas/"
                "LROE_PF_140_1_1_Ingresos_ConfacturaConSG_AltaRespuesta_V1_0_2.xsd"
            ),
            "root_element": "LROEPF140IngresosConFacturaConSGAltaRespuesta",
            "operation_nsmap": "lrpjfecsgap",
        },
        LROEOperationTypeEnum.resp_cancel_sg_invoice_pj_240.value: {
            "operation_ns": (
                "https://www.batuz.eus/fitxategiak/batuz/LROE/esquemas/"
                "LROE_PJ_240_1_1_FacturasEmitidas_ConSG_AnulacionRespuesta_V1_0_0.xsd"
            ),
            "root_element": "LROEPJ240FacturasEmitidasConSGAnulacionRespuesta",
            "operation_nsmap": "lrpjfecsgap",
        },
        LROEOperationTypeEnum.resp_cancel_sg_invoice_pf_140.value: {
            "operation_ns": (
                "https://www.batuz.eus/fitxategiak/batuz/LROE/esquemas/"
                "LROE_PF_140_1_1_Ingresos_ConfacturaConSG_AnulacionRespuesta_V1_0_0.xsd"
            ),
            "root_element": "LROEPF140IngresosConFacturaConSGAnulacionRespuesta",
            "operation_nsmap": "lrpjfecsgap",
        },
        LROEOperationTypeEnum.alta_invoice_in_pj_240.value: {
            "operation_ns": (
                "https://www.batuz.eus/fitxategiak/batuz/LROE/esquemas/"
                "LROE_PJ_240_2_FacturasRecibidas_AltaModifPeticion_V1_0_1.xsd"
            ),
            "root_element": "LROEPJ240FacturasRecibidasAltaModifPeticion",
            "operation_nsmap": "lrpjframp",
        },
        LROEOperationTypeEnum.alta_invoice_in_pf_140.value: {
            "operation_ns": (
                "https://www.batuz.eus/fitxategiak/batuz/LROE/esquemas/"
                "LROE_PF_140_2_1_Gastos_Confactura_AltaModifPeticion_V1_0_2.xsd"
            ),
            "root_element": "LROEPF140GastosConFacturaAltaModifPeticion",
            "operation_nsmap": "lrpfgcfamp",
        },
        LROEOperationTypeEnum.cancel_invoice_in_pj_240.value: {
            "operation_ns": (
                "https://www.batuz.eus/fitxategiak/batuz/LROE/esquemas/"
                "LROE_PJ_240_2_FacturasRecibidas_AnulacionPeticion_V1_0_0.xsd"
            ),
            "root_element": "LROEPJ240FacturasRecibidasAnulacionPeticion",
            "operation_nsmap": "lrpjfrap",
        },
        LROEOperationTypeEnum.cancel_invoice_in_pf_140.value: {
            "operation_ns": (
                "https://www.batuz.eus/fitxategiak/batuz/LROE/esquemas/"
                "LROE_PF_140_2_1_Gastos_Confactura_AnulacionPeticion_V1_0_0.xsd"
            ),
            "root_element": "LROEPF140GastosConFacturaAnulacionPeticion",
            "operation_nsmap": "lrpfgcfap",
        },
        LROEOperationTypeEnum.resp_alta_invoice_in_pj_240.value: {
            "operation_ns": (
                "https://www.batuz.eus/fitxategiak/batuz/LROE/esquemas/"
                "LROE_PJ_240_2_FacturasRecibidas_AltaModifRespuesta_V1_0_1.xsd"
            ),
            "root_element": "LROEPJ240FacturasRecibidasAltaModifRespuesta",
            "operation_nsmap": "lrpjframr",
        },
        LROEOperationTypeEnum.resp_alta_invoice_in_pf_140.value: {
            "operation_ns": (
                "https://www.batuz.eus/fitxategiak/batuz/LROE/esquemas/"
                "LROE_PF_140_2_1_Gastos_Confactura_AltaModifRespuesta_V1_0_1.xsd"
            ),
            "root_element": "LROEPF140GastosConFacturaAltaModifRespuesta",
            "operation_nsmap": "lrpfgcfamr",
        },
        LROEOperationTypeEnum.resp_cancel_invoice_in_pj_240.value: {
            "operation_ns": (
                "https://www.batuz.eus/fitxategiak/batuz/LROE/esquemas/"
                "LROE_PJ_240_2_FacturasRecibidas_AnulacionRespuesta_V1_0_0.xsd"
            ),
            "root_element": "LROEPJ240FacturasRecibidasAnulacionRespuesta",
            "operation_nsmap": "lrpjfrar",
        },
        LROEOperationTypeEnum.resp_cancel_invoice_in_pf_140.value: {
            "operation_ns": (
                "https://www.batuz.eus/fitxategiak/batuz/LROE/esquemas/"
                "LROE_PF_140_2_1_Gastos_Confactura_AnulacionRespuesta_V1_0_0.xsd"
            ),
            "root_element": "LROEPF140GastosConFacturaAnulacionRespuesta",
            "operation_nsmap": "lrpfgcfar",
        },
    }

    def __init__(self, mode):
        if mode in self.lroe_operation_data.keys():
            self.lroe_operation_ns = self.lroe_operation_data[mode]["operation_ns"]
            self.root_element = self.lroe_operation_data[mode]["root_element"]
            lroe_operation_nsmap = self.lroe_operation_data[mode]["operation_nsmap"]
        else:
            raise LROEXMLSchemaModeNotSupported("LROE - XML mode not supported!")
        self.mode = mode
        self.lroe_operation_nsmap = {lroe_operation_nsmap: self.lroe_operation_ns}

    @staticmethod
    def xml_is_valid(test_xmlschema_doc, root):
        """
        :param test_xmlschema_doc: Parsed XSD file with Xades imports
        :param root: xml
        :return: bool
        """
        schema = etree.XMLSchema(test_xmlschema_doc)
        return schema(root)

    def create_node_from_dict(self, xml_root, key, value):
        if isinstance(value, dict):
            xml_element = etree.SubElement(xml_root, key)
            for subkey, subvalue in value.items():
                self.create_node_from_dict(xml_element, subkey, subvalue)
        elif isinstance(value, list):
            for list_element in value:
                xml_element = etree.SubElement(xml_root, key)
                # NOTE: All list elements are expected to be of type dict
                for subkey, subvalue in list_element.items():
                    self.create_node_from_dict(xml_element, subkey, subvalue)
        else:
            xml_element = etree.SubElement(xml_root, key)
            xml_element.text = value

    def dict2xml(self, lroe_operation_ordered_dict):
        tag = next(iter(lroe_operation_ordered_dict))
        root = etree.Element(
            "{%s}%s" % (self.lroe_operation_ns, tag), nsmap=self.lroe_operation_nsmap
        )
        lroe_operation_dict = lroe_operation_ordered_dict.get(tag)
        for key, value in lroe_operation_dict.items():
            self.create_node_from_dict(root, key, value)
        return root

    def parse_xml(self, xml):
        """
        Parse TicketBAI response XML
        :param xml: XML string
        :return: OrderedDict
        """
        namespaces = {self.lroe_operation_ns: None}
        return xmltodict.parse(xml, process_namespaces=True, namespaces=namespaces)
