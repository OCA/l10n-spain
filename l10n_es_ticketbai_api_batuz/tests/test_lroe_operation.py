# Copyright (2021) Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import datetime
import gzip
import json
import os

from lxml import etree

from odoo.tests.common import tagged

from odoo.addons.l10n_es_ticketbai_api.tests.common import TestL10nEsTicketBAIAPI

from ..lroe import lroe_api
from ..lroe.lroe_xml_schema import LROEXMLSchema, LROEXMLSchemaModeNotSupported
from ..models.lroe_operation import LROEModelEnum, LROEOperationEnum
from ..models.lroe_operation_response import (
    LROEOperationResponseLineState,
    LROEOperationResponseState,
)

TEST_01_XSD_SCHEMA = "LROE_PJ_240_1_1_FacturasEmitidas_ConSG_AltaPeticion_V1_0_2.xsd"
TEST_02_XSD_SCHEMA = "LROE_PF_140_1_1_Ingresos_ConfacturaConSG_AltaPeticion_V1_0_2.xsd"
TEST_03_XSD_SCHEMA = (
    "LROE_PJ_240_1_1_FacturasEmitidas_ConSG_AnulacionPeticion_V1_0_0.xsd"
)
TEST_04_XSD_SCHEMA = (
    "LROE_PF_140_1_1_Ingresos_ConfacturaConSG_AnulacionPeticion_V1_0_0.xsd"
)
TEST_EXEC_PATH = os.path.dirname(os.path.abspath(__file__))
TEST_RESPONSE_DIR = os.path.join(TEST_EXEC_PATH, "lroe_response_files")
TEST_05_RESPONSE_GZ_FILENAME = os.path.join(
    TEST_RESPONSE_DIR,
    "Ejemplo_1_LROE_PJ_240_FacturasEmitidasConSG_B00000034_Correcta_Resp.gz",
)
TEST_06_RESPONSE_GZ_FILENAME = os.path.join(
    TEST_RESPONSE_DIR,
    "Ejemplo_1_LROE_PF_140_IngresosConFacturaConSG_79732487C_Correcta_Resp.gz",
)
TEST_07_RESPONSE_GZ_FILENAME = os.path.join(
    TEST_RESPONSE_DIR,
    "Ejemplo_1_LROE_PJ_240_FacturasEmitidasConSG_B00000034_Parc_Correcta_Resp.gz",
)
TEST_08_RESPONSE_GZ_FILENAME = os.path.join(
    TEST_RESPONSE_DIR,
    "Ejemplo_1_LROE_PF_140_IngresosConFacturaConSG_79732487C_Parc_Correcta_Resp.gz",
)
TEST_09_RESPONSE_GZ_FILENAME = os.path.join(
    TEST_RESPONSE_DIR,
    "Ejemplo_1_LROE_PJ_240_FacturasEmitidasConSG_B00000034_Incorrecta_Resp.gz",
)
TEST_10_RESPONSE_GZ_FILENAME = os.path.join(
    TEST_RESPONSE_DIR,
    "Ejemplo_Anulacion_1_LROE_PF_140_IngresosConFacturaConSG_79732487C_Correcta_Resp.gz",
)


# include lroe catalog in the list of loaded catalogs
TestL10nEsTicketBAIAPI.catalogs.append(
    "file:"
    + (os.path.join(os.path.abspath(os.path.dirname(__file__)), "schemas/catalog.xml"))
)


@tagged("post_install", "-at_install")
class TestL10nEsTicketBAIAPIBatuz(TestL10nEsTicketBAIAPI):
    def create_tbai_cancel_invoice(self, str_number):
        uid = self.tech_user.id
        invoice = self.create_tbai_national_invoice_cancellation(
            name="TBAITEST/" + str_number,
            company_id=self.main_company.id,
            number=str_number,
            number_prefix="TBAITEST/",
            uid=uid,
        )
        invoice.build_tbai_invoice()
        return invoice

    def create_tbai_invoice(self, str_number):
        uid = self.tech_user.id
        invoice = self.create_tbai_national_invoice(
            name="TBAITEST/" + str_number,
            company_id=self.main_company.id,
            number=str_number,
            number_prefix="TBAITEST/",
            uid=uid,
        )
        self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
        invoice.build_tbai_invoice()
        return invoice

    def _prepare_bizkaia_company(self, company):
        test_dir_path = os.path.abspath(os.path.dirname(__file__))
        pj_240 = "company-bizkaia-pj-240.json"
        pf_140 = "company-bizkaia-pf-140.json"
        p12_pj_240 = "tbai-p12-bizkaia-pj-240.json"
        p12_pf_140 = "tbai-p12-bizkaia-pf-140.json"
        lroe_240 = LROEModelEnum.model_pj_240.value
        lroe_model = company.lroe_model
        company_json = pj_240 if lroe_model == lroe_240 else pf_140
        tbai_p12_json = p12_pj_240 if lroe_model == lroe_240 else p12_pf_140
        tbai_p12_json_path = os.path.join(test_dir_path, tbai_p12_json)
        self.company_values_json_filepath = os.path.join(test_dir_path, company_json)
        with open(self.company_values_json_filepath) as fp:
            company_vals = json.load(fp)
        if "invoice_number" in company_vals:
            company_vals.pop("invoice_number")
        if "refund_invoice_number" in company_vals:
            company_vals.pop("refund_invoice_number")
        with open(tbai_p12_json_path) as fp:
            p12_vals = json.load(fp)
            cert_path = os.path.join(
                test_dir_path, p12_vals.pop("tbai_p12_certificate_path")
            )
            cert_password = p12_vals.pop("tbai_p12_certificate_password")
            certificate = self.create_certificate(company.id, cert_path, cert_password)
        company_vals.update(
            {
                "tbai_certificate_id": certificate.id,
                "tbai_tax_agency_id": self.env.ref(
                    "l10n_es_ticketbai_api_batuz.tbai_tax_agency_bizkaia"
                ).id,
            }
        )
        tbai_developer_json = os.path.join(
            test_dir_path, "tbai-batuz-soft-developer.json"
        )
        with open(tbai_developer_json) as fp:
            developer_vals = json.load(fp)
        tbai_installation = self.env["tbai.installation"].create(
            {
                "name": developer_vals.pop("name"),
                "version": developer_vals.pop("version"),
                "developer_id": self.env["res.partner"]
                .create(
                    {"name": "TBai Bizkaia Developer", "vat": developer_vals.pop("vat")}
                )
                .id,
                "license_key": developer_vals.pop("license_key"),
            }
        )
        company_vals.update({"tbai_installation_id": tbai_installation.id})
        company.write(company_vals)

    def setUp(self):
        super().setUp()
        self.lroe_op_model = self.env["lroe.operation"]
        schemas_version_dirname = LROEXMLSchema.schemas_version_dirname
        script_dirpath = os.path.abspath(os.path.dirname(__file__))
        schemas_dirpath = os.path.join(script_dirpath, "schemas")
        lroe_240_chapter_1 = self.env.ref(
            "l10n_es_ticketbai_api_batuz.lroe_chapter_pj_240_1"
        )
        lroe_240_subchapter_1 = self.env.ref(
            "l10n_es_ticketbai_api_batuz.lroe_subchapter_pj_240_1_1"
        )
        lroe_140_chapter_1 = self.env.ref(
            "l10n_es_ticketbai_api_batuz.lroe_chapter_pf_140_1"
        )
        lroe_140_subchapter_1 = self.env.ref(
            "l10n_es_ticketbai_api_batuz.lroe_subchapter_pf_140_1_1"
        )
        # Load XSD file with XADES imports
        test_01_xsd_filepath = os.path.abspath(
            os.path.join(
                schemas_dirpath, "%s/%s" % (schemas_version_dirname, TEST_01_XSD_SCHEMA)
            )
        )
        self.test_01_schema_doc = etree.parse(
            test_01_xsd_filepath, parser=etree.ETCompatXMLParser()
        )
        test_02_xsd_filepath = os.path.abspath(
            os.path.join(
                schemas_dirpath, "%s/%s" % (schemas_version_dirname, TEST_02_XSD_SCHEMA)
            )
        )
        self.test_02_schema_doc = etree.parse(
            test_02_xsd_filepath, parser=etree.ETCompatXMLParser()
        )
        test_03_xsd_filepath = os.path.abspath(
            os.path.join(
                schemas_dirpath, "%s/%s" % (schemas_version_dirname, TEST_03_XSD_SCHEMA)
            )
        )
        self.test_03_schema_doc = etree.parse(
            test_03_xsd_filepath, parser=etree.ETCompatXMLParser()
        )
        test_04_xsd_filepath = os.path.abspath(
            os.path.join(
                schemas_dirpath, "%s/%s" % (schemas_version_dirname, TEST_04_XSD_SCHEMA)
            )
        )
        self.test_04_schema_doc = etree.parse(
            test_04_xsd_filepath, parser=etree.ETCompatXMLParser()
        )
        self.lroe_240_chapter_1 = lroe_240_chapter_1
        self.lroe_240_subchapter_1 = lroe_240_subchapter_1
        self.lroe_140_chapter_1 = lroe_140_chapter_1
        self.lroe_140_subchapter_1 = lroe_140_subchapter_1

    def test_lroe_xml_schema_unknown_raises(self):
        with self.assertRaises(LROEXMLSchemaModeNotSupported):
            LROEXMLSchema("unsupporte")

    def test_01_xml_alta_model_pj_240(self):
        tbai_invoice1_ids = self.create_tbai_invoice("00001")
        tbai_invoice2_ids = self.create_tbai_invoice("00002")
        tbai_invoice_ids = tbai_invoice1_ids.ids + tbai_invoice2_ids.ids
        self.main_company.lroe_model = LROEModelEnum.model_pj_240.value
        lroe_op_alta_pj_240_dict = {
            "company_id": self.main_company.id,
            "type": LROEOperationEnum.create.value,
            "tbai_invoice_ids": [(6, 0, tbai_invoice_ids)],
            "lroe_chapter_id": self.lroe_240_chapter_1.id,
            "lroe_subchapter_id": self.lroe_240_subchapter_1.id,
        }
        lroe_op_alta_model_pj_240 = self.lroe_op_model.create(lroe_op_alta_pj_240_dict)
        lroe_xml_root = lroe_op_alta_model_pj_240.get_lroe_operations_xml()
        res = LROEXMLSchema.xml_is_valid(self.test_01_schema_doc, lroe_xml_root)
        self.assertTrue(res)
        # check gzip compression
        lroe_op_alta_model_pj_240.xml_datas = base64.encodebytes(b"<e>RAWTEXT</e>")
        lroe_op_alta_model_pj_240.xml_datas_fname = "rawtext.xml"
        data_len, data = lroe_op_alta_model_pj_240.set_trx_gzip_file()
        self.assertTrue(int(data_len) > 0)
        self.assertEqual(b"<e>RAWTEXT</e>", gzip.decompress(data))
        self.assertEqual(
            b"<e>RAWTEXT</e>",
            gzip.decompress(
                base64.decodebytes(lroe_op_alta_model_pj_240.trx_gzip_file)
            ),
        )
        values = self.env["lroe.operation.response"].prepare_lroe_error_values(
            lroe_op_alta_model_pj_240, "MSG_CONTENT"
        )
        self.assertTrue(values["description"].endswith("MSG_CONTENT"))
        self.assertTrue(values)

    def test_02_xml_alta_model_pf_140(self):
        tbai_invoice1_ids = self.create_tbai_invoice("00001")
        tbai_invoice2_ids = self.create_tbai_invoice("00002")
        tbai_invoice_ids = tbai_invoice1_ids.ids + tbai_invoice2_ids.ids
        self.main_company.lroe_model = LROEModelEnum.model_pf_140.value
        self.main_company.main_activity_iae = "276300"
        lroe_op_alta_pf_140_dict = {
            "company_id": self.main_company.id,
            "type": LROEOperationEnum.create.value,
            "tbai_invoice_ids": [(6, 0, tbai_invoice_ids)],
            "lroe_chapter_id": self.lroe_140_chapter_1.id,
            "lroe_subchapter_id": self.lroe_140_subchapter_1.id,
        }
        lroe_op_alta_model_pf_140 = self.lroe_op_model.create(lroe_op_alta_pf_140_dict)
        lroe_xml_root = lroe_op_alta_model_pf_140.get_lroe_operations_xml()
        res = LROEXMLSchema.xml_is_valid(self.test_02_schema_doc, lroe_xml_root)
        self.assertTrue(res)
        res = LROEXMLSchema.xml_is_valid(self.test_01_schema_doc, lroe_xml_root)
        self.assertFalse(res)

    def test_03_xml_cancel_model_pj_240(self):
        tbai_invoice1_cancel_ids = self.create_tbai_cancel_invoice("00001")
        tbai_invoice2_cancel_ids = self.create_tbai_cancel_invoice("00002")
        tbai_cancel_invoice_ids = (
            tbai_invoice1_cancel_ids.ids + tbai_invoice2_cancel_ids.ids
        )
        self.main_company.lroe_model = LROEModelEnum.model_pj_240.value
        lroe_op_cancel_pj_240_dict = {
            "company_id": self.main_company.id,
            "type": LROEOperationEnum.cancel.value,
            "tbai_invoice_ids": [(6, 0, tbai_cancel_invoice_ids)],
            "lroe_chapter_id": self.lroe_240_chapter_1.id,
            "lroe_subchapter_id": self.lroe_240_subchapter_1.id,
        }
        lroe_op_cancel_model_pj_240 = self.lroe_op_model.create(
            lroe_op_cancel_pj_240_dict
        )
        lroe_xml_root = lroe_op_cancel_model_pj_240.get_lroe_operations_xml()
        res = LROEXMLSchema.xml_is_valid(self.test_03_schema_doc, lroe_xml_root)
        self.assertTrue(res)

    def test_04_xml_cancel_model_pf_140(self):
        tbai_invoice1_cancel_ids = self.create_tbai_cancel_invoice("00001")
        tbai_invoice2_cancel_ids = self.create_tbai_cancel_invoice("00002")
        tbai_cancel_invoice_ids = (
            tbai_invoice1_cancel_ids.ids + tbai_invoice2_cancel_ids.ids
        )
        self.main_company.lroe_model = LROEModelEnum.model_pf_140.value
        self.main_company.main_activity_iae = "276300"
        lroe_op_cancel_pf_140_dict = {
            "company_id": self.main_company.id,
            "type": LROEOperationEnum.cancel.value,
            "tbai_invoice_ids": [(6, 0, tbai_cancel_invoice_ids)],
            "lroe_chapter_id": self.lroe_140_chapter_1.id,
            "lroe_subchapter_id": self.lroe_140_subchapter_1.id,
        }
        lroe_op_cancel_model_pf_140 = self.lroe_op_model.create(
            lroe_op_cancel_pf_140_dict
        )
        lroe_xml_root = lroe_op_cancel_model_pf_140.get_lroe_operations_xml()
        res = LROEXMLSchema.xml_is_valid(self.test_04_schema_doc, lroe_xml_root)
        self.assertTrue(res)

    def test_05_prepare_lroe_response_values_alta_model_pj_240(self):
        tbai_invoice_obj = self.create_tbai_invoice("00001")
        self.main_company.lroe_model = LROEModelEnum.model_pj_240.value
        lroe_op_alta_pj_240_dict = {
            "company_id": self.main_company.id,
            "type": LROEOperationEnum.create.value,
            "tbai_invoice_ids": [(6, 0, [tbai_invoice_obj.id])],
            "lroe_chapter_id": self.lroe_240_chapter_1.id,
            "lroe_subchapter_id": self.lroe_240_subchapter_1.id,
        }
        lroe_op_alta_model_pj_240 = self.lroe_op_model.create(lroe_op_alta_pj_240_dict)
        response_headers = {
            "date": str(datetime.datetime.now()),
            "eus-bizkaia-n3-tipo-respuesta": "Correcto",
            "eus-bizkaia-n3-identificativo": "1",
            "eus-bizkaia-n3-numero-registro": "1001",
        }
        with open(TEST_05_RESPONSE_GZ_FILENAME, "rb") as response_data_file:
            lroe_srv_response = lroe_api.LROEOperationResponse(
                data=gzip.decompress(response_data_file.read()),
                headers=response_headers,
            )
            lroe_response_values = self.env[
                "lroe.operation.response"
            ].prepare_lroe_response_values(lroe_srv_response, lroe_op_alta_model_pj_240)
        self.assertEqual(
            lroe_response_values.get("lroe_operation_id"), lroe_op_alta_model_pj_240.id
        )
        self.assertEqual(
            lroe_response_values.get("state"), LROEOperationResponseState.CORRECT.value
        )
        self.assertTrue(len(lroe_response_values.get("xml")) > 0)
        self.assertTrue(len(lroe_response_values.get("response_line_ids")) > 0)
        for response_line_id in lroe_response_values.get("response_line_ids"):
            self.assertTrue(
                response_line_id[2].get("state"),
                LROEOperationResponseLineState.CORRECT.value,
            )

    def test_06_prepare_lroe_response_values_alta_model_pf_140(self):
        tbai_invoice_obj = self.create_tbai_invoice("00001")
        self.main_company.lroe_model = LROEModelEnum.model_pf_140.value
        self.main_company.main_activity_iae = "276300"
        lroe_op_alta_pf_140_dict = {
            "company_id": self.main_company.id,
            "type": LROEOperationEnum.create.value,
            "tbai_invoice_ids": [(6, 0, [tbai_invoice_obj.id])],
            "lroe_chapter_id": self.lroe_140_chapter_1.id,
            "lroe_subchapter_id": self.lroe_140_subchapter_1.id,
        }
        lroe_op_alta_model_pf_140 = self.lroe_op_model.create(lroe_op_alta_pf_140_dict)
        response_headers = {
            "date": str(datetime.datetime.now()),
            "eus-bizkaia-n3-tipo-respuesta": "Correcto",
            "eus-bizkaia-n3-identificativo": "1",
            "eus-bizkaia-n3-numero-registro": "1001",
        }
        with open(TEST_06_RESPONSE_GZ_FILENAME, "rb") as response_data_file:
            lroe_srv_response = lroe_api.LROEOperationResponse(
                data=gzip.decompress(response_data_file.read()),
                headers=response_headers,
            )
            lroe_response_values = self.env[
                "lroe.operation.response"
            ].prepare_lroe_response_values(lroe_srv_response, lroe_op_alta_model_pf_140)
        self.assertEqual(
            lroe_response_values.get("lroe_operation_id"), lroe_op_alta_model_pf_140.id
        )
        self.assertEqual(
            lroe_response_values.get("state"), LROEOperationResponseState.CORRECT.value
        )
        self.assertTrue(len(lroe_response_values.get("xml")) > 0)
        self.assertTrue(len(lroe_response_values.get("response_line_ids")) > 0)
        for response_line_id in lroe_response_values.get("response_line_ids"):
            self.assertTrue(
                response_line_id[2].get("state"),
                LROEOperationResponseLineState.CORRECT.value,
            )

    def test_07_prepare_lroe_response_values_alta_model_pj_240_w_errors(self):
        tbai_invoice_obj = self.create_tbai_invoice("00001")
        self.main_company.lroe_model = LROEModelEnum.model_pj_240.value
        lroe_op_alta_pj_240_dict = {
            "company_id": self.main_company.id,
            "type": LROEOperationEnum.create.value,
            "tbai_invoice_ids": [(6, 0, [tbai_invoice_obj.id])],
            "lroe_chapter_id": self.lroe_240_chapter_1.id,
            "lroe_subchapter_id": self.lroe_240_subchapter_1.id,
        }
        lroe_op_alta_model_pj_240 = self.lroe_op_model.create(lroe_op_alta_pj_240_dict)
        response_headers = {
            "date": str(datetime.datetime.now()),
            "eus-bizkaia-n3-tipo-respuesta": "ParcialmenteCorrecto",
            "eus-bizkaia-n3-identificativo": "1",
            "eus-bizkaia-n3-numero-registro": "1001",
        }
        with open(TEST_07_RESPONSE_GZ_FILENAME, "rb") as response_data_file:
            lroe_srv_response = lroe_api.LROEOperationResponse(
                data=gzip.decompress(response_data_file.read()),
                headers=response_headers,
            )
            lroe_response_values = self.env[
                "lroe.operation.response"
            ].prepare_lroe_response_values(lroe_srv_response, lroe_op_alta_model_pj_240)
        self.assertEqual(
            lroe_response_values.get("lroe_operation_id"), lroe_op_alta_model_pj_240.id
        )
        self.assertEqual(
            lroe_response_values.get("state"),
            LROEOperationResponseState.PARTIALLY_CORRECT.value,
        )
        self.assertTrue(len(lroe_response_values.get("xml")) > 0)
        self.assertTrue(len(lroe_response_values.get("response_line_ids")) > 0)
        response_correct = 0
        response_incorrect = 0
        for response_line_id in lroe_response_values.get("response_line_ids"):
            response_line_dict = response_line_id[2]
            if (
                response_line_dict.get("state")
                == LROEOperationResponseLineState.CORRECT.value
            ):
                response_correct += 1
            if (
                response_line_dict.get("state")
                == LROEOperationResponseLineState.INCORRECT.value
            ):
                response_incorrect += 1
                self.assertTrue(len(response_line_dict.get("code")) > 0)
                self.assertTrue(len(response_line_dict.get("description")) > 0)
        self.assertTrue(response_correct, 1)
        self.assertTrue(response_incorrect, 1)

    def test_08_prepare_lroe_response_values_alta_model_pf_140_w_errors(self):
        tbai_invoice_obj = self.create_tbai_invoice("00001")
        self.main_company.lroe_model = LROEModelEnum.model_pf_140.value
        self.main_company.main_activity_iae = "276300"
        lroe_op_alta_pf_140_dict = {
            "company_id": self.main_company.id,
            "type": LROEOperationEnum.create.value,
            "tbai_invoice_ids": [(6, 0, [tbai_invoice_obj.id])],
            "lroe_chapter_id": self.lroe_140_chapter_1.id,
            "lroe_subchapter_id": self.lroe_140_subchapter_1.id,
        }
        lroe_op_alta_model_pf_140 = self.lroe_op_model.create(lroe_op_alta_pf_140_dict)
        response_headers = {
            "date": str(datetime.datetime.now()),
            "eus-bizkaia-n3-tipo-respuesta": "ParcialmenteCorrecto",
            "eus-bizkaia-n3-identificativo": "1",
            "eus-bizkaia-n3-numero-registro": "1001",
        }
        with open(TEST_08_RESPONSE_GZ_FILENAME, "rb") as response_data_file:
            lroe_srv_response = lroe_api.LROEOperationResponse(
                data=gzip.decompress(response_data_file.read()),
                headers=response_headers,
            )
            lroe_response_values = self.env[
                "lroe.operation.response"
            ].prepare_lroe_response_values(lroe_srv_response, lroe_op_alta_model_pf_140)
        self.assertEqual(
            lroe_response_values.get("lroe_operation_id"), lroe_op_alta_model_pf_140.id
        )
        self.assertEqual(
            lroe_response_values.get("state"),
            LROEOperationResponseState.PARTIALLY_CORRECT.value,
        )
        self.assertTrue(len(lroe_response_values.get("xml")) > 0)
        self.assertTrue(len(lroe_response_values.get("response_line_ids")) > 0)
        response_correct = 0
        response_incorrect = 0
        for response_line_id in lroe_response_values.get("response_line_ids"):
            response_line_dict = response_line_id[2]
            if (
                response_line_dict.get("state")
                == LROEOperationResponseLineState.CORRECT.value
            ):
                response_correct += 1
            if (
                response_line_dict.get("state")
                == LROEOperationResponseLineState.INCORRECT.value
            ):
                response_incorrect += 1
                self.assertTrue(len(response_line_dict.get("code")) > 0)
                self.assertTrue(len(response_line_dict.get("description")) > 0)
        self.assertTrue(response_correct, 1)
        self.assertTrue(response_incorrect, 1)

    def test_09_prepare_lroe_response_values_alta_model_pj_240_incorrect(self):
        tbai_invoice_obj = self.create_tbai_invoice("00001")
        self.main_company.lroe_model = LROEModelEnum.model_pj_240.value
        lroe_op_alta_pj_240_dict = {
            "company_id": self.main_company.id,
            "type": LROEOperationEnum.create.value,
            "tbai_invoice_ids": [(6, 0, [tbai_invoice_obj.id])],
            "lroe_chapter_id": self.lroe_240_chapter_1.id,
            "lroe_subchapter_id": self.lroe_240_subchapter_1.id,
        }
        lroe_op_alta_model_pj_240 = self.lroe_op_model.create(lroe_op_alta_pj_240_dict)
        response_headers = {
            "date": str(datetime.datetime.now()),
            "eus-bizkaia-n3-tipo-respuesta": "Incorrecto",
        }
        with open(TEST_09_RESPONSE_GZ_FILENAME, "rb") as response_data_file:
            lroe_srv_response = lroe_api.LROEOperationResponse(
                data=gzip.decompress(response_data_file.read()),
                headers=response_headers,
            )
            lroe_response_values = self.env[
                "lroe.operation.response"
            ].prepare_lroe_response_values(lroe_srv_response, lroe_op_alta_model_pj_240)
        self.assertEqual(
            lroe_response_values.get("lroe_operation_id"), lroe_op_alta_model_pj_240.id
        )
        self.assertEqual(
            lroe_response_values.get("state"),
            LROEOperationResponseState.INCORRECT.value,
        )
        self.assertTrue(len(lroe_response_values.get("xml")) > 0)
        self.assertTrue(len(lroe_response_values.get("response_line_ids")) > 0)
        for response_line_id in lroe_response_values.get("response_line_ids"):
            self.assertEqual(
                response_line_id[2].get("state"),
                LROEOperationResponseLineState.INCORRECT.value,
            )

    def test_10_prepare_lroe_response_values_cancel_model_pf_140(self):
        tbai_invoice_obj = self.create_tbai_cancel_invoice("00001")
        self.main_company.lroe_model = LROEModelEnum.model_pf_140.value
        self.main_company.main_activity_iae = "276300"
        lroe_op_cancel_pf_140_dict = {
            "company_id": self.main_company.id,
            "type": LROEOperationEnum.cancel.value,
            "tbai_invoice_ids": [(6, 0, [tbai_invoice_obj.id])],
            "lroe_chapter_id": self.lroe_140_chapter_1.id,
            "lroe_subchapter_id": self.lroe_140_subchapter_1.id,
        }
        lroe_op_cancel_model_pf_140 = self.lroe_op_model.create(
            lroe_op_cancel_pf_140_dict
        )
        response_headers = {
            "date": str(datetime.datetime.now()),
            "eus-bizkaia-n3-tipo-respuesta": "Correcto",
            "eus-bizkaia-n3-identificativo": "1",
            "eus-bizkaia-n3-numero-registro": "1001",
        }
        with open(TEST_10_RESPONSE_GZ_FILENAME, "rb") as response_data_file:
            lroe_srv_response = lroe_api.LROEOperationResponse(
                data=gzip.decompress(response_data_file.read()),
                headers=response_headers,
            )
            lroe_response_values = self.env[
                "lroe.operation.response"
            ].prepare_lroe_response_values(
                lroe_srv_response, lroe_op_cancel_model_pf_140
            )
        self.assertEqual(
            lroe_response_values.get("lroe_operation_id"),
            lroe_op_cancel_model_pf_140.id,
        )
        self.assertEqual(
            lroe_response_values.get("state"), LROEOperationResponseState.CORRECT.value
        )
        self.assertTrue(len(lroe_response_values.get("xml")) > 0)
        self.assertTrue(len(lroe_response_values.get("response_line_ids")) > 0)
        for response_line_id in lroe_response_values.get("response_line_ids"):
            self.assertTrue(
                response_line_id[2].get("state"),
                LROEOperationResponseLineState.CORRECT.value,
            )

    def test_get_tbai_state(self):
        LroeOperationResponse = self.env["lroe.operation.response"]
        states = [
            (
                LROEOperationResponseState.BUILD_ERROR.value,
                LROEOperationResponseState.BUILD_ERROR.value,
            ),
            (
                LROEOperationResponseState.REQUEST_ERROR.value,
                LROEOperationResponseState.REQUEST_ERROR.value,
            ),
            (LROEOperationResponseState.CORRECT.value, "00"),
            (LROEOperationResponseState.INCORRECT.value, "01"),
            (LROEOperationResponseState.PARTIALLY_CORRECT.value, "00"),
            (LROEOperationResponseLineState.CORRECT_WITH_ERRORS.value, "00"),
        ]
        for in_state, out_state in states:
            s = LroeOperationResponse.get_tbai_state(in_state)
            self.assertEqual(s, out_state)

    def test_alta_pj_240_send_to_tax_agency(self):
        if self.send_to_tax_agency:
            self.main_company.lroe_model = LROEModelEnum.model_pj_240.value
            self._prepare_bizkaia_company(self.main_company)
            invoice_number_str = self.get_next_number()
            tbai_invoice_id = self.create_tbai_invoice(invoice_number_str)
            self._send_to_tax_agency(tbai_invoice_id)

    def test_alta_model_pf_140_send_to_tax_agency(self):
        if self.send_to_tax_agency:
            self.main_company.lroe_model = LROEModelEnum.model_pf_140.value
            self._prepare_bizkaia_company(self.main_company)
            invoice_number_str = self.get_next_number()
            tbai_invoice_id = self.create_tbai_invoice(invoice_number_str)
            self._send_to_tax_agency(tbai_invoice_id)

    def test_cancel_model_pj_240_send_to_tax_agency(self):
        if self.send_to_tax_agency:
            self.main_company.lroe_model = LROEModelEnum.model_pj_240.value
            self._prepare_bizkaia_company(self.main_company)
            invoice_number_str = self.get_next_number()
            tbai_invoice_id = self.create_tbai_invoice(invoice_number_str)
            self._send_to_tax_agency(tbai_invoice_id)
            tbai_cancel_invoice_id = self.create_tbai_cancel_invoice(invoice_number_str)
            self._send_to_tax_agency(tbai_cancel_invoice_id)

    def test_cancel_model_pf_140_send_to_tax_agency(self):
        if self.send_to_tax_agency:
            self.main_company.lroe_model = LROEModelEnum.model_pf_140.value
            self._prepare_bizkaia_company(self.main_company)
            invoice_number_str = self.get_next_number()
            tbai_invoice_id = self.create_tbai_invoice(invoice_number_str)
            self._send_to_tax_agency(tbai_invoice_id)
            tbai_cancel_invoice_id = self.create_tbai_cancel_invoice(invoice_number_str)
            self._send_to_tax_agency(tbai_cancel_invoice_id)
