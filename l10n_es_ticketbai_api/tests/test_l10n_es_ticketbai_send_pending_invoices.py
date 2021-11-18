# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import common
from .common import TestL10nEsTicketBAIAPI


@common.at_install(False)
@common.post_install(True)
class TestL10nEsTicketBAIInvoice(TestL10nEsTicketBAIAPI):

    def test_send_pending_invoices_never_raises(self):
        def raise_exception():
            raise Exception("Raised on test_send_pending_invoices_never_raises")
        Invoice = self.env['tbai.invoice']
        Invoice.send_pending_invoices_impl = raise_exception
        Invoice.send_pending_invoices()

    def test_send_pending_invoices_wrong_db(self):
        Parameter = self.env['ir.config_parameter']
        Parameter.set_param('database.ticketbai', self.env.cr.dbname + '-xxx')

        def get_next_pending_invoice_raise(*args, **kwargs):
            raise Exception("This should not be called")
        Invoice = self.env['tbai.invoice']
        Invoice.get_next_pending_invoice = get_next_pending_invoice_raise
        Invoice.send_pending_invoices()

    def test_send_pending_invoices(self):
        invoice = None
        response = None

        def return_response(*args, **kwargs):
            return response

        def get_next_pending_invoice(*args, **kwargs):
            if not getattr(invoice, '_testing_consumed', False):
                invoice.state = 'pending'
                invoice._testing_consumed = True
                return invoice
            return None

        invoice = self.create_tbai_national_invoice()
        invoice.send = return_response
        invoice.get_next_pending_invoice = get_next_pending_invoice

        invoice._testing_consumed = False
        response = self.env['tbai.response'].create({
            'tbai_invoice_id': invoice.id,
            'state': '00'
        })
        invoice.send_pending_invoices()
        self.assertEqual(invoice.state, 'sent')

        invoice._testing_consumed = False
        response = self.env['tbai.response'].create({
            'tbai_invoice_id': invoice.id,
            'state': '01'
        })
        invoice.send_pending_invoices()
        self.assertEqual(invoice.state, 'error')

        invoice._testing_consumed = False
        response = self.env['tbai.response'].create({
            'tbai_invoice_id': invoice.id,
            'state': '-1'
        })
        invoice.send_pending_invoices()
        self.assertEqual(invoice.state, 'pending')

        invoice._testing_consumed = False
        response = self.env['tbai.response'].create({
            'tbai_invoice_id': invoice.id,
            'state': '-2'
        })
        invoice.send_pending_invoices()
        self.assertEqual(invoice.state, 'pending')

    def test_prepare_tbai_response_values(self):

        def response_message(estado):
            return ('''
<TicketBaiResponse>
   <Salida>
      <IdentificadorTBAI>TBAI-00000006Y-251019-btFpwP8dcLGAF-
237</IdentificadorTBAI>
      <FechaRecepcion>01-03-2020 12:31:34</FechaRecepcion>
      <Estado>%(estado)s</Estado>
      <Descripcion>DESC_ES</Descripcion>
      <Azalpena>DESC_EU</Azalpena>
      <ResultadosValidacion>
          <Codigo>002</Codigo>
          <Descripcion>VAL_DESC_ES</Descripcion>
          <Azalpena>Mezuak ez du XSDaren egitura betetzen</Azalpena>
      </ResultadosValidacion>
      <CSV>TBAI33076dde-180d-4484-88ff-094ba2e93587</CSV>
   </Salida>
</TicketBaiResponse>
''' % locals()).strip()

        class B1:
            error = True
            errno = 'errno'
            strerror = 'strerror'
        r = self.env['tbai.response'].prepare_tbai_response_values(B1())
        self.assertTrue(r)

        class B2:
            error = False
            errno = 'errno'
            strerror = 'strerror'
            data = response_message('00')
        r = self.env['tbai.response'].prepare_tbai_response_values(B2())
        self.assertTrue(r)
        self.assertEqual(r['state'], '00')
        self.assertEqual(
            r['tbai_response_message_ids'][0][2]['description']['es_ES'],
            'DESC_ES')
        self.assertEqual(
            r['tbai_response_message_ids'][1][2]['description']['es_ES'],
            'VAL_DESC_ES')

        class B3:
            error = False
            errno = 'errno'
            strerror = 'strerror'
            data = response_message('01')
        r = self.env['tbai.response'].prepare_tbai_response_values(B3())
        self.assertTrue(r)
        self.assertEqual(r['state'], '01')
        self.assertEqual(
            r['tbai_response_message_ids'][0][2]['description']['es_ES'],
            'VAL_DESC_ES')

        class B4:
            error = False
            errno = 'errno'
            strerror = 'strerror'
            data = response_message('xx')
        r = self.env['tbai.response'].prepare_tbai_response_values(B4())
        self.assertTrue(r)
        self.assertEqual(r['state'], 'xx')
