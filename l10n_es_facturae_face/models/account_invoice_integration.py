# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import models, fields, _
import logging
import base64
from .wsse_signature import MemorySignature

_logger = logging.getLogger(__name__)
try:
    from OpenSSL import crypto
    from zeep import Client
except (ImportError, IOError) as err:
    _logger.info(err)


class AccountInvoiceIntegration(models.Model):
    _inherit = "account.invoice.integration"

    integration_status = fields.Selection(selection_add=[
        ('face-1200', 'Registered on REC'),
        ('face-1300', 'Registered on RCF'),
        ('face-2400', 'Accepted'),
        ('face-2500', 'Payed'),
        ('face-2600', 'Rejected'),
        ('face-3100', 'Cancellation approved'),
    ])
    cancellation_status = fields.Selection(selection_add=[
        ('face-4100', 'Not requested'),
        ('face-4200', 'Cancellation requested'),
        ('face-4300', 'Cancellation accepted'),
        ('face-4400', 'Cancellation rejected'),
    ])
    company_id = fields.Many2one(
        "res.company", related="invoice_id.company_id", store=True)

    def _cron_face_update_method(self, company_domain=False):
        if not company_domain:
            company_domain = []
        face = self.env.ref('l10n_es_facturae_face.integration_face')
        for company in self.env['res.company'].search(company_domain):
            integrations = self.search([
                ('company_id', '=', company.id),
                ('method_id', '=', face.id),
                ('state', '=', 'sent'),
                '|',
                ('integration_status', '=', False),
                ('integration_status', 'in', [
                    'face-1200', 'face-1300', 'face-2400'
                ]),
            ])
            if not integrations:
                continue
            cert = crypto.load_pkcs12(
                base64.b64decode(company.facturae_cert),
                company.facturae_cert_password
            )
            cert.set_ca_certificates(None)
            client = Client(
                wsdl=self.env["ir.config_parameter"].sudo().get_param(
                    "account.invoice.face.server", default=None),
                wsse=MemorySignature(
                    cert.export(),
                    base64.b64decode(
                        self.env.ref(
                            'l10n_es_facturae_face.face_certificate').datas
                    ),
                )
            )
            integration_dict = {}
            integration_list = []
            for integration in integrations:
                integration_list.append(integration.register_number)
                integration_dict[integration.register_number] = integration
            request = client.get_type('ns0:ConsultarListadoFacturaRequest')(
                integration_list
            )
            response = client.service.consultarListadoFacturas(request)
            if response.resultado.codigo != '0':
                _logger.info(_('Company %s cannot be processed') % company.display_name)
                continue
            for invoice in response.facturas.consultarListadoFactura:
                integ = integration_dict[invoice.factura.numeroRegistro]
                factura = invoice.factura
                if invoice.codigo != '0':
                    # Probably processed from another system
                    continue
                process_code = 'face-' + factura.tramitacion.codigo
                revocation_code = 'face-' + factura.anulacion.codigo
                if (
                    integ.integration_status == process_code and
                    integ.cancellation_status == revocation_code
                ):
                    # Nothing has changed on the invoice
                    continue
                log = self.env['account.invoice.integration.log'].create(
                    integ.update_values())
                log.state = 'sent'
                integ.integration_status = process_code
                integ.integration_description = factura.tramitacion.motivo
                integ.cancellation_status = revocation_code
                integ.cancellation_description = factura.anulacion.motivo
                if integ.cancellation_status != 'face-4100':
                    integ.can_cancel = False
