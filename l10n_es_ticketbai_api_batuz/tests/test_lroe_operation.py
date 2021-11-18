# Copyright (2021) Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import os
import base64
import datetime
import gzip
from odoo.tests import common
from ..models.lroe_operation import LROEOperationEnum, LROEModelEnum
from ..models.lroe_operation_response\
    import LROEOperationResponseState, LROEOperationResponseLineState
from ..lroe import lroe_api
from odoo.addons.l10n_es_ticketbai_api.tests.common import TestL10nEsTicketBAIAPI
from ..lroe.lroe_xml_schema import LROEXMLSchema, LROEXMLSchemaModeNotSupported
from lxml import etree

TEST_01_XSD_SCHEMA =\
    'Test-LROE_PJ_240_1_1_FacturasEmitidas_ConSG_AltaPeticion_V1_0_2.xsd'
TEST_02_XSD_SCHEMA =\
    'Test-LROE_PF_140_1_1_Ingresos_ConfacturaConSG_AltaPeticion_V1_0_2.xsd'
TEST_03_XSD_SCHEMA =\
    'Test-LROE_PJ_240_1_1_FacturasEmitidas_ConSG_AnulacionPeticion_V1_0_0.xsd'
TEST_04_XSD_SCHEMA =\
    'Test-LROE_PF_140_1_1_Ingresos_ConfacturaConSG_AnulacionPeticion_V1_0_0.xsd'
TEST_EXEC_PATH = os.path.dirname(os.path.abspath(__file__))
TEST_RESPONSE_DIR = os.path.join(TEST_EXEC_PATH, 'lroe_response_files')
TEST_05_RESPONSE_GZ_FILENAME = os.path.join(
    TEST_RESPONSE_DIR,
    'Ejemplo_1_LROE_PJ_240_FacturasEmitidasConSG_B00000034_Correcta_Resp.gz')
TEST_06_RESPONSE_GZ_FILENAME = os.path.join(
    TEST_RESPONSE_DIR,
    'Ejemplo_1_LROE_PF_140_IngresosConFacturaConSG_79732487C_Correcta_Resp.gz')
TEST_07_RESPONSE_GZ_FILENAME = os.path.join(
    TEST_RESPONSE_DIR,
    'Ejemplo_1_LROE_PJ_240_FacturasEmitidasConSG_B00000034_Parc_Correcta_Resp.gz')
TEST_08_RESPONSE_GZ_FILENAME = os.path.join(
    TEST_RESPONSE_DIR,
    'Ejemplo_1_LROE_PF_140_IngresosConFacturaConSG_79732487C_Parc_Correcta_Resp.gz')
TEST_09_RESPONSE_GZ_FILENAME = os.path.join(
    TEST_RESPONSE_DIR,
    'Ejemplo_1_LROE_PJ_240_FacturasEmitidasConSG_B00000034_Incorrecta_Resp.gz')
TEST_10_RESPONSE_GZ_FILENAME = os.path.join(
    TEST_RESPONSE_DIR,
    'Ejemplo_Anulacion_1_LROE_PF_140_IngresosConFacturaConSG_79732487C_Correcta_Resp.gz'
)


# include lroe catalog in the list of loaded catalogs
TestL10nEsTicketBAIAPI.catalogs.append(
    'file:' + (os.path.join(
        os.path.abspath(
            os.path.dirname(__file__)), 'schemas/catalog.xml'))
)


@common.at_install(False)
@common.post_install(True)
class TestL10nEsTicketBAIAPIBatuz(TestL10nEsTicketBAIAPI):

    def create_tbai_cancel_invoice(self, str_number):
        uid = self.tech_user.id
        invoice = self.create_tbai_national_invoice_cancellation(
            name='TBAITEST/' + str_number,
            company_id=self.main_company.id, number=str_number,
            number_prefix='TBAITEST/', uid=uid)
        invoice.build_tbai_invoice()
        return invoice

    def create_tbai_invoice(self, str_number):
        uid = self.tech_user.id
        invoice = self.create_tbai_national_invoice(
            name='TBAITEST/' + str_number,
            company_id=self.main_company.id,
            number=str_number,
            number_prefix='TBAITEST/',
            uid=uid)
        self.add_customer_from_odoo_partner_to_invoice(invoice.id, self.partner)
        invoice.build_tbai_invoice()
        return invoice

    def setUp(self):
        super().setUp()
        self.lroe_op_model = self.env['lroe.operation']
        schemas_version_dirname = LROEXMLSchema.schemas_version_dirname
        script_dirpath = os.path.abspath(os.path.dirname(__file__))
        schemas_dirpath = os.path.join(script_dirpath, 'schemas')
        # Load XSD file with XADES imports
        test_01_xsd_filepath = os.path.abspath(
            os.path.join(schemas_dirpath,
                         '%s/%s' % (schemas_version_dirname, TEST_01_XSD_SCHEMA)))
        self.test_01_schema_doc = etree.parse(
            test_01_xsd_filepath,
            parser=etree.ETCompatXMLParser())
        test_02_xsd_filepath = os.path.abspath(
            os.path.join(schemas_dirpath,
                         '%s/%s' % (schemas_version_dirname, TEST_02_XSD_SCHEMA)))
        self.test_02_schema_doc = etree.parse(
            test_02_xsd_filepath,
            parser=etree.ETCompatXMLParser())
        test_03_xsd_filepath = os.path.abspath(
            os.path.join(schemas_dirpath,
                         '%s/%s' % (schemas_version_dirname, TEST_03_XSD_SCHEMA)))
        self.test_03_schema_doc = etree.parse(
            test_03_xsd_filepath,
            parser=etree.ETCompatXMLParser())
        test_04_xsd_filepath = os.path.abspath(
            os.path.join(schemas_dirpath,
                         '%s/%s' % (schemas_version_dirname, TEST_04_XSD_SCHEMA)))
        self.test_04_schema_doc = etree.parse(
            test_04_xsd_filepath,
            parser=etree.ETCompatXMLParser())

    def test_lroe_xml_schema_unknown_raises(self):
        with self.assertRaises(LROEXMLSchemaModeNotSupported):
            LROEXMLSchema("unsupporte")

    def test_01_xml_alta_model_pj_240(self):
        tbai_invoice1_ids = self.create_tbai_invoice('00001')
        tbai_invoice2_ids = self.create_tbai_invoice('00002')
        tbai_invoice_ids = tbai_invoice1_ids.ids + tbai_invoice2_ids.ids
        self.main_company.lroe_model = LROEModelEnum.model_pj_240.value
        lroe_op_alta_pj_240_dict = {
            'company_id': self.main_company.id,
            'type': LROEOperationEnum.create.value,
            'tbai_invoice_ids': [(6, 0, tbai_invoice_ids)]
        }
        lroe_op_alta_model_pj_240 = self.lroe_op_model.create(lroe_op_alta_pj_240_dict)
        lroe_xml_root = lroe_op_alta_model_pj_240.get_lroe_operations_xml()
        res = LROEXMLSchema.xml_is_valid(self.test_01_schema_doc, lroe_xml_root)
        self.assertTrue(res)
        # check gzip compression
        lroe_op_alta_model_pj_240.xml_datas = base64.encodebytes(b'<e>RAWTEXT</e>')
        lroe_op_alta_model_pj_240.xml_datas_fname = 'rawtext.xml'
        data_len, data = lroe_op_alta_model_pj_240.set_trx_gzip_file()
        self.assertTrue(int(data_len) > 0)
        self.assertEqual(b'<e>RAWTEXT</e>', gzip.decompress(data))
        self.assertEqual(
            b'<e>RAWTEXT</e>',
            gzip.decompress(
                base64.decodebytes(lroe_op_alta_model_pj_240.trx_gzip_file)))
        values = self.env['lroe.operation.response'].prepare_lroe_error_values(
            lroe_op_alta_model_pj_240,
            'MSG_CONTENT'
        )
        self.assertTrue(values['description'].endswith('MSG_CONTENT'))
        self.assertTrue(values)

    def test_02_xml_alta_model_pf_140(self):
        tbai_invoice1_ids = self.create_tbai_invoice('00001')
        tbai_invoice2_ids = self.create_tbai_invoice('00002')
        tbai_invoice_ids = tbai_invoice1_ids.ids + tbai_invoice2_ids.ids
        self.main_company.lroe_model = LROEModelEnum.model_pf_140.value
        lroe_op_alta_pf_140_dict = {
            'company_id': self.main_company.id,
            'type': LROEOperationEnum.create.value,
            'tbai_invoice_ids': [(6, 0, tbai_invoice_ids)]
        }
        lroe_op_alta_model_pf_140 = self.lroe_op_model.create(lroe_op_alta_pf_140_dict)
        lroe_xml_root = lroe_op_alta_model_pf_140.get_lroe_operations_xml()
        res = LROEXMLSchema.xml_is_valid(self.test_02_schema_doc, lroe_xml_root)
        self.assertTrue(res)
        res = LROEXMLSchema.xml_is_valid(self.test_01_schema_doc, lroe_xml_root)
        self.assertFalse(res)

    def test_03_xml_cancel_model_pj_240(self):
        tbai_invoice1_cancel_ids = self.create_tbai_cancel_invoice('00001')
        tbai_invoice2_cancel_ids = self.create_tbai_cancel_invoice('00002')
        tbai_cancel_invoice_ids = tbai_invoice1_cancel_ids.ids\
            + tbai_invoice2_cancel_ids.ids
        self.main_company.lroe_model = LROEModelEnum.model_pj_240.value
        lroe_op_cancel_pj_240_dict = {
            'company_id': self.main_company.id,
            'type': LROEOperationEnum.cancel.value,
            'tbai_invoice_ids': [(6, 0, tbai_cancel_invoice_ids)]
        }
        lroe_op_cancel_model_pj_240 = self.lroe_op_model.create(
            lroe_op_cancel_pj_240_dict
        )
        lroe_xml_root = lroe_op_cancel_model_pj_240.get_lroe_operations_xml()
        res = LROEXMLSchema.xml_is_valid(self.test_03_schema_doc, lroe_xml_root)
        self.assertTrue(res)

    def test_04_xml_cancel_model_pf_140(self):
        tbai_invoice1_cancel_ids = self.create_tbai_cancel_invoice('00001')
        tbai_invoice2_cancel_ids = self.create_tbai_cancel_invoice('00002')
        tbai_cancel_invoice_ids = tbai_invoice1_cancel_ids.ids +\
            tbai_invoice2_cancel_ids.ids
        self.main_company.lroe_model = LROEModelEnum.model_pf_140.value
        lroe_op_cancel_pf_140_dict = {
            'company_id': self.main_company.id,
            'type': LROEOperationEnum.cancel.value,
            'tbai_invoice_ids': [(6, 0, tbai_cancel_invoice_ids)]
        }
        lroe_op_cancel_model_pf_140 = self.lroe_op_model.create(
            lroe_op_cancel_pf_140_dict
        )
        lroe_xml_root = lroe_op_cancel_model_pf_140.get_lroe_operations_xml()
        res = LROEXMLSchema.xml_is_valid(self.test_04_schema_doc, lroe_xml_root)
        self.assertTrue(res)

    def test_05_prepare_lroe_response_values_alta_model_pj_240(self):
        tbai_invoice_obj = self.create_tbai_invoice('00001')
        self.main_company.lroe_model = LROEModelEnum.model_pj_240.value
        lroe_op_alta_pj_240_dict = {
            'company_id': self.main_company.id,
            'type': LROEOperationEnum.create.value,
            'tbai_invoice_ids': [(6, 0, [tbai_invoice_obj.id])]
        }
        lroe_op_alta_model_pj_240 = self.lroe_op_model.create(lroe_op_alta_pj_240_dict)
        response_headers = {
            'date': str(datetime.datetime.now()),
            'eus-bizkaia-n3-tipo-respuesta': 'Correcto',
            'eus-bizkaia-n3-identificativo': '1',
            'eus-bizkaia-n3-numero-registro': '1001'}
        with open(TEST_05_RESPONSE_GZ_FILENAME, 'rb') as response_data_file:
            lroe_srv_response = lroe_api.LROEOperationResponse(
                data=gzip.decompress(response_data_file.read()),
                headers=response_headers)
            lroe_response_values = \
                self.env['lroe.operation.response'].prepare_lroe_response_values(
                    lroe_srv_response,
                    lroe_op_alta_model_pj_240)
        self.assertEqual(
            lroe_response_values.get('lroe_operation_id'),
            lroe_op_alta_model_pj_240.id)
        self.assertEqual(
            lroe_response_values.get('state'),
            LROEOperationResponseState.CORRECT.value)
        self.assertTrue(len(lroe_response_values.get('xml')) > 0)
        self.assertTrue(len(lroe_response_values.get('response_line_ids')) > 0)
        for response_line_id in lroe_response_values.get('response_line_ids'):
            self.assertTrue(
                response_line_id[2].get('state'),
                LROEOperationResponseLineState.CORRECT.value)

    def test_06_prepare_lroe_response_values_alta_model_pf_140(self):
        tbai_invoice_obj = self.create_tbai_invoice('00001')
        self.main_company.lroe_model = LROEModelEnum.model_pf_140.value
        lroe_op_alta_pf_140_dict = {
            'company_id': self.main_company.id,
            'type': LROEOperationEnum.create.value,
            'tbai_invoice_ids': [(6, 0, [tbai_invoice_obj.id])]
        }
        lroe_op_alta_model_pf_140 = self.lroe_op_model.create(lroe_op_alta_pf_140_dict)
        response_headers = {
            'date': str(datetime.datetime.now()),
            'eus-bizkaia-n3-tipo-respuesta': 'Correcto',
            'eus-bizkaia-n3-identificativo': '1',
            'eus-bizkaia-n3-numero-registro': '1001'}
        with open(TEST_06_RESPONSE_GZ_FILENAME, 'rb') as response_data_file:
            lroe_srv_response = lroe_api.LROEOperationResponse(
                data=gzip.decompress(response_data_file.read()),
                headers=response_headers)
            lroe_response_values = self.env['lroe.operation.response']\
                .prepare_lroe_response_values(
                    lroe_srv_response,
                    lroe_op_alta_model_pf_140)
        self.assertEqual(
            lroe_response_values.get('lroe_operation_id'),
            lroe_op_alta_model_pf_140.id)
        self.assertEqual(
            lroe_response_values.get('state'),
            LROEOperationResponseState.CORRECT.value)
        self.assertTrue(len(lroe_response_values.get('xml')) > 0)
        self.assertTrue(len(lroe_response_values.get('response_line_ids')) > 0)
        for response_line_id in lroe_response_values.get('response_line_ids'):
            self.assertTrue(
                response_line_id[2].get('state'),
                LROEOperationResponseLineState.CORRECT.value)

    def test_07_prepare_lroe_response_values_alta_model_pj_240_w_errors(self):
        tbai_invoice_obj = self.create_tbai_invoice('00001')
        self.main_company.lroe_model = LROEModelEnum.model_pj_240.value
        lroe_op_alta_pj_240_dict = {
            'company_id': self.main_company.id,
            'type': LROEOperationEnum.create.value,
            'tbai_invoice_ids': [(6, 0, [tbai_invoice_obj.id])]
        }
        lroe_op_alta_model_pj_240 = self.lroe_op_model.create(lroe_op_alta_pj_240_dict)
        response_headers = {
            'date': str(datetime.datetime.now()),
            'eus-bizkaia-n3-tipo-respuesta': 'Parcialmente correcto',
            'eus-bizkaia-n3-identificativo': '1',
            'eus-bizkaia-n3-numero-registro': '1001'}
        with open(TEST_07_RESPONSE_GZ_FILENAME, 'rb') as response_data_file:
            lroe_srv_response = lroe_api.LROEOperationResponse(
                data=gzip.decompress(response_data_file.read()),
                headers=response_headers)
            lroe_response_values = \
                self.env['lroe.operation.response'].prepare_lroe_response_values(
                    lroe_srv_response,
                    lroe_op_alta_model_pj_240)
        self.assertEqual(
            lroe_response_values.get('lroe_operation_id'),
            lroe_op_alta_model_pj_240.id)
        self.assertEqual(
            lroe_response_values.get('state'),
            LROEOperationResponseState.PARTIALLY_CORRECT.value)
        self.assertTrue(len(lroe_response_values.get('xml')) > 0)
        self.assertTrue(len(lroe_response_values.get('response_line_ids')) > 0)
        response_correct = 0
        response_incorrect = 0
        for response_line_id in lroe_response_values.get('response_line_ids'):
            response_line_dict = response_line_id[2]
            if response_line_dict.get('state') ==\
               LROEOperationResponseLineState.CORRECT.value:
                response_correct += 1
            if response_line_dict.get('state') ==\
               LROEOperationResponseLineState.INCORRECT.value:
                response_incorrect += 1
                self.assertTrue(len(response_line_dict.get('code')) > 0)
                self.assertTrue(len(response_line_dict.get('description')) > 0)
        self.assertTrue(response_correct, 1)
        self.assertTrue(response_incorrect, 1)

    def test_08_prepare_lroe_response_values_alta_model_pf_140_w_errors(self):
        tbai_invoice_obj = self.create_tbai_invoice('00001')
        self.main_company.lroe_model = LROEModelEnum.model_pf_140.value
        lroe_op_alta_pf_140_dict = {
            'company_id': self.main_company.id,
            'type': LROEOperationEnum.create.value,
            'tbai_invoice_ids': [(6, 0, [tbai_invoice_obj.id])]
        }
        lroe_op_alta_model_pf_140 = self.lroe_op_model.create(lroe_op_alta_pf_140_dict)
        response_headers = {
            'date': str(datetime.datetime.now()),
            'eus-bizkaia-n3-tipo-respuesta': 'Parcialmente correcto',
            'eus-bizkaia-n3-identificativo': '1',
            'eus-bizkaia-n3-numero-registro': '1001'}
        with open(TEST_08_RESPONSE_GZ_FILENAME, 'rb') as response_data_file:
            lroe_srv_response = lroe_api.LROEOperationResponse(
                data=gzip.decompress(response_data_file.read()),
                headers=response_headers)
            lroe_response_values = self.env['lroe.operation.response']\
                .prepare_lroe_response_values(
                    lroe_srv_response,
                    lroe_op_alta_model_pf_140)
        self.assertEqual(
            lroe_response_values.get('lroe_operation_id'),
            lroe_op_alta_model_pf_140.id)
        self.assertEqual(
            lroe_response_values.get('state'),
            LROEOperationResponseState.PARTIALLY_CORRECT.value)
        self.assertTrue(len(lroe_response_values.get('xml')) > 0)
        self.assertTrue(len(lroe_response_values.get('response_line_ids')) > 0)
        response_correct = 0
        response_incorrect = 0
        for response_line_id in lroe_response_values.get('response_line_ids'):
            response_line_dict = response_line_id[2]
            if response_line_dict.get('state')\
               == LROEOperationResponseLineState.CORRECT.value:
                response_correct += 1
            if response_line_dict.get('state')\
               == LROEOperationResponseLineState.INCORRECT.value:
                response_incorrect += 1
                self.assertTrue(len(response_line_dict.get('code')) > 0)
                self.assertTrue(len(response_line_dict.get('description')) > 0)
        self.assertTrue(response_correct, 1)
        self.assertTrue(response_incorrect, 1)

    def test_09_prepare_lroe_response_values_alta_model_pj_240_incorrect(self):
        tbai_invoice_obj = self.create_tbai_invoice('00001')
        self.main_company.lroe_model = LROEModelEnum.model_pj_240.value
        lroe_op_alta_pj_240_dict = {
            'company_id': self.main_company.id,
            'type': LROEOperationEnum.create.value,
            'tbai_invoice_ids': [(6, 0, [tbai_invoice_obj.id])]
        }
        lroe_op_alta_model_pj_240 = self.lroe_op_model.create(lroe_op_alta_pj_240_dict)
        response_headers = {
            'date': str(datetime.datetime.now()),
            'eus-bizkaia-n3-tipo-respuesta': 'Incorrecto'
        }
        with open(TEST_09_RESPONSE_GZ_FILENAME, 'rb') as response_data_file:
            lroe_srv_response = lroe_api.LROEOperationResponse(
                data=gzip.decompress(response_data_file.read()),
                headers=response_headers)
            lroe_response_values = \
                self.env['lroe.operation.response'].prepare_lroe_response_values(
                    lroe_srv_response,
                    lroe_op_alta_model_pj_240)
        self.assertEqual(
            lroe_response_values.get('lroe_operation_id'),
            lroe_op_alta_model_pj_240.id)
        self.assertEqual(
            lroe_response_values.get('state'),
            LROEOperationResponseState.INCORRECT.value)
        self.assertTrue(len(lroe_response_values.get('xml')) > 0)
        self.assertTrue(len(lroe_response_values.get('response_line_ids')) > 0)
        for response_line_id in lroe_response_values.get('response_line_ids'):
            self.assertEqual(
                response_line_id[2].get('state'),
                LROEOperationResponseLineState.INCORRECT.value)

    def test_10_prepare_lroe_response_values_cancel_model_pf_140(self):
        tbai_invoice_obj = self.create_tbai_cancel_invoice('00001')
        self.main_company.lroe_model = LROEModelEnum.model_pf_140.value
        lroe_op_cancel_pf_140_dict = {
            'company_id': self.main_company.id,
            'type': LROEOperationEnum.cancel.value,
            'tbai_invoice_ids': [(6, 0, [tbai_invoice_obj.id])]
        }
        lroe_op_cancel_model_pf_140 = self.lroe_op_model.create(
            lroe_op_cancel_pf_140_dict)
        response_headers = {
            'date': str(datetime.datetime.now()),
            'eus-bizkaia-n3-tipo-respuesta': 'Correcto',
            'eus-bizkaia-n3-identificativo': '1',
            'eus-bizkaia-n3-numero-registro': '1001'
        }
        with open(TEST_10_RESPONSE_GZ_FILENAME, 'rb') as response_data_file:
            lroe_srv_response = lroe_api.LROEOperationResponse(
                data=gzip.decompress(response_data_file.read()),
                headers=response_headers)
            lroe_response_values = \
                self.env['lroe.operation.response'].prepare_lroe_response_values(
                    lroe_srv_response,
                    lroe_op_cancel_model_pf_140)
        self.assertEqual(
            lroe_response_values.get('lroe_operation_id'),
            lroe_op_cancel_model_pf_140.id)
        self.assertEqual(
            lroe_response_values.get('state'),
            LROEOperationResponseState.CORRECT.value)
        self.assertTrue(len(lroe_response_values.get('xml')) > 0)
        self.assertTrue(len(lroe_response_values.get('response_line_ids')) > 0)
        for response_line_id in lroe_response_values.get('response_line_ids'):
            self.assertTrue(
                response_line_id[2].get('state'),
                LROEOperationResponseLineState.CORRECT.value)

    def test_get_tbai_state(self):
        LroeOperationResponse = self.env['lroe.operation.response']
        states = [
            (
                LROEOperationResponseState.BUILD_ERROR.value,
                LROEOperationResponseState.BUILD_ERROR.value
            ),
            (
                LROEOperationResponseState.REQUEST_ERROR.value,
                LROEOperationResponseState.REQUEST_ERROR.value
            ),
            (
                LROEOperationResponseState.CORRECT.value,
                '00'
            ),
            (
                LROEOperationResponseState.INCORRECT.value,
                '01'
            ),
            (
                LROEOperationResponseState.PARTIALLY_CORRECT.value,
                '00'),
            (
                LROEOperationResponseLineState.CORRECT_WITH_ERRORS.value,
                '00'
            ),
        ]
        for in_state, out_state in states:
            s = LroeOperationResponse.get_tbai_state(
                in_state
            )
            self.assertEqual(s, out_state)
