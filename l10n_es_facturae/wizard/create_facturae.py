# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Alejandro Sanchez (http://www.asr-oss.com)
#    Alejandro Sanchez <alejandro@asr-oss.com>
#    Copyright (c) 2015 Comunitea Servicios Tecnológicos
#    Omar Castiñeira Saavedra <omar@comunitea.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the Affero GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the Affero GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import base64
from openerp import models, fields, _, api, exceptions
import logging
import subprocess
import os
from unidecode import unidecode

logger = logging.Logger("facturae")


class Log(Exception):
    def __init__(self):
        self.content = ""
        self.error = False

    def add(self, s, error=True):
        self.content = self.content + s
        if error:
            self.error = error

    def __call__(self):
        return self.content

    def __str__(self):
        return self.content


class CreateFacturae(models.TransientModel):

    _name = "create.facturae"

    facturae = fields.Binary('Factura-E file', readonly=True)
    facturae_fname = fields.Char("File name", size=64)
    note = fields.Text('Log')
    state = fields.Selection([('first', 'First'), ('second', 'Second')],
                             'State', readonly=True, default='first')
    firmar_facturae = fields.\
        Boolean('¿Desea firmar digitalmente el fichero generado?',
                help='Requiere certificado en la ficha de la compañía')

    @api.multi
    def end_document_hook(self, xml_facturae):
        return xml_facturae

    @api.multi
    def create_facturae_file(self):

        def _format_xml():
            # formato y definicion del fichero xml
            texto = '<fe:Facturae xmlns:fe=' \
                    '"http://www.facturae.es/Facturae/2009/v3.2/Facturae" ' \
                    'xmlns:ds="http://www.w3.org/2000/09/xmldsig#">'
            return texto

        def _persona(vat):
            texto = ''
            if vat[2:3].isdigit():
                texto = 'F'
            else:
                texto = 'J'
            return texto

        def _apoyo_batch():
            texto = ''
            currency = invoice.currency_id

            texto += '<TotalInvoicesAmount>'
            texto += '<TotalAmount>' + str('%.2f' % invoice.amount_total) \
                     + '</TotalAmount>'
            texto += '</TotalInvoicesAmount>'

            texto += '<TotalOutstandingAmount>'
            texto += '<TotalAmount>' + str('%.2f' % invoice.amount_total) \
                     + '</TotalAmount>'
            texto += '</TotalOutstandingAmount>'

            texto += '<TotalExecutableAmount>'
            texto += '<TotalAmount>' + str('%.2f' % invoice.amount_total) \
                     + '</TotalAmount>'
            texto += '</TotalExecutableAmount>'
            texto += '<InvoiceCurrencyCode>' + currency.name \
                     + '</InvoiceCurrencyCode>'

            return texto

        def _header_facturae():

            company_partner_obj = invoice.company_id.partner_id

            schemaversion = '3.2'
            modality = 'I'

            if not invoice.number:
                log.add(_('User error:\n\nCan not create Factura-E '
                          'file if invoice has no number.'))
                raise log

            if company_partner_obj.vat:
                BatchIdentifier = invoice.number + company_partner_obj.vat
            else:
                log.add(_('User error:\n\nCompany %s has no VAT number.') %
                        company_partner_obj.name, True)
                raise log

            texto = ''
            texto += '<FileHeader>'
            texto += '<SchemaVersion>' + schemaversion + '</SchemaVersion>'
            texto += '<Modality>' + modality + '</Modality>'
            texto += '<InvoiceIssuerType>EM</InvoiceIssuerType>'
            texto += '<Batch>'
            texto += '<BatchIdentifier>' + BatchIdentifier +\
                     '</BatchIdentifier>'
            texto += '<InvoicesCount>1</InvoicesCount>'
            texto += _apoyo_batch()
            texto += '</Batch>'
            texto += '</FileHeader>'
            return texto

        def _parties_facturae():

            company_obj = invoice.company_id
            company_partner_obj = company_obj.partner_id
            invoice_partner_obj = invoice.partner_id.commercial_partner_id
            invoice_partner_address_obj = invoice.partner_id
            contact_partner_address_obj = invoice.partner_id

            # obtencion de la direccion del partner
            # partner_address_invoice = invoice.partner_id
            if company_partner_obj.vat:
                tipo_seller = _persona(company_partner_obj.vat)
            else:
                log.add(_('User error:\n\nCompany %s does not have '
                          'a VAT number.') % company_partner_obj.name, True)
                raise log

            if invoice_partner_obj.vat:
                tipo_buyer = _persona(invoice_partner_obj.vat)
            else:
                log.add(_('User error:\n\nPartner %s does not have '
                          'a VAT number.') % invoice_partner_obj.name, True)
                raise log

            texto = ''
            texto += '<Parties>'
            texto += '<SellerParty>'
            texto += '<TaxIdentification>'
            texto += '<PersonTypeCode>' + tipo_seller + '</PersonTypeCode>'
            texto += '<ResidenceTypeCode>R</ResidenceTypeCode>'
            texto += '<TaxIdentificationNumber>' + company_partner_obj.vat \
                     + '</TaxIdentificationNumber>'
            texto += '</TaxIdentification>'

            if tipo_seller == 'F':
                texto += '<Individual>'
                texto += '<Name>' + company_partner_obj.name + '</Name>'
                texto += '<FirstSurname></FirstSurname>'
                texto += '<SecondSurname></SecondSurname>'
            else:
                texto += '<LegalEntity>'
                texto += '<CorporateName>' + company_partner_obj.name +\
                         '</CorporateName>'
                texto += '<TradeName>' + company_partner_obj.name +\
                         '</TradeName>'

            texto += '<AddressInSpain>'
            if company_partner_obj.street:
                if company_partner_obj.street2:
                    texto += '<Address>' + company_partner_obj.street +\
                             u' ' + company_partner_obj.street2 + '</Address>'
                else:
                    texto += '<Address>' + company_partner_obj.street +\
                             '</Address>'
            else:
                log.add(_('User error:\n\nCompany %s has no street.') %
                        company_partner_obj.name, True)
                raise log
            if company_partner_obj.zip:
                texto += '<PostCode>' + company_partner_obj.zip + '</PostCode>'
            else:
                log.add(_('User error:\n\nCompany %s has no zip code.') %
                        company_partner_obj.name, True)
                raise log
            if company_partner_obj.city:
                texto += '<Town>' + company_partner_obj.city + '</Town>'
            else:
                log.add(_('User error:\n\nCompany %s has no city.') %
                        company_partner_obj.name, True)
                raise log
            if company_partner_obj.state_id.name:
                texto += '<Province>' + company_partner_obj.state_id.name +\
                         '</Province>'
            else:
                log.add(_('User error:\n\nCompany %s has no province.') %
                        company_partner_obj.name, True)
                raise log
            if company_partner_obj.country_id.code_3166:
                texto += '<CountryCode>' + \
                         company_partner_obj.country_id.code_3166 +\
                         '</CountryCode>'
            else:
                log.add(_('User error:\n\nCompany %s has no country.') %
                        company_partner_obj.name, True)
                raise log
            texto += '</AddressInSpain>'

            texto += '<ContactDetails>'
            if company_partner_obj.phone:
                texto += '<Telephone>' + company_partner_obj.phone +\
                         '</Telephone>'
            if company_partner_obj.fax:
                texto += '<TeleFax>' + company_partner_obj.fax + '</TeleFax>'
            if company_partner_obj.website:
                texto += '<WebAddress>' + \
                         company_partner_obj.website + '</WebAddress>'
            if company_partner_obj.email:
                texto += '<ElectronicMail>' + \
                         company_partner_obj.email + '</ElectronicMail>'
            if company_partner_obj.name:
                texto += '<ContactPersons>' + \
                         company_partner_obj.name + '</ContactPersons>'
            texto += '</ContactDetails>'

            if tipo_seller == 'F':
                texto += '</Individual>'
            else:
                texto += '</LegalEntity>'

            texto += '</SellerParty>'
            texto += '<BuyerParty>'
            texto += '<TaxIdentification>'
            texto += '<PersonTypeCode>' + tipo_buyer + '</PersonTypeCode>'
            texto += '<ResidenceTypeCode>R</ResidenceTypeCode>'
            texto += '<TaxIdentificationNumber>' + \
                     invoice_partner_obj.vat + '</TaxIdentificationNumber>'
            texto += '</TaxIdentification>'

            administrative = False
            if invoice_partner_address_obj.facturae:
                texto += "<AdministrativeCentres>"
                administrative = True

            def create_administrative_centres(address, code):
                texto = ""
                if administrative:
                    if code == '01':
                        texto += "<AdministrativeCentre>"
                        texto += "<CentreCode>" + address.oficina_contable[:10] +\
                                 "</CentreCode>"
                        texto += "<RoleTypeCode>" + code + "</RoleTypeCode>"
                    elif code == '02':
                        texto += "<AdministrativeCentre>"
                        texto += "<CentreCode>" + address.organo_gestor[:20] +\
                                 "</CentreCode>"
                        texto += "<RoleTypeCode>" + code + "</RoleTypeCode>"
                    elif code == '03':
                        texto += "<AdministrativeCentre>"
                        texto += "<CentreCode>" + address.unidad_tramitadora[:20] +\
                                 "</CentreCode>"
                        texto += "<RoleTypeCode>" + code + "</RoleTypeCode>"
                    elif code == '04':
                        texto += "<AdministrativeCentre>"
                        texto += "<CentreCode>" + address.organo_proponente[:20] +\
                                 "</CentreCode>"
                        texto += "<RoleTypeCode>" + code + "</RoleTypeCode>"
                    else:
                        texto += "<AdministrativeCentre>"
                        texto += "<CentreCode>" + '' + "</CentreCode>"
                        texto += "<RoleTypeCode>" + code + "</RoleTypeCode>"

                texto += '<AddressInSpain>'
                if address.street:
                    if address.street2:
                        texto += '<Address>' + (address.street + ' ' + \
                                 address.street2)[:80] + '</Address>'
                    else:
                        texto += '<Address>' + address.street[:80] + '</Address>'
                else:
                    log.add(_('User error:\n\nPartner %s has no street.') %
                            address.name, True)
                    raise log
                if address.zip:
                    texto += '<PostCode>' + address.zip[:9] + '</PostCode>'
                else:
                    log.add(_('User error:\n\nPartner %s has no zip code.') %
                            address.name, True)
                    raise log

                if address.city:
                    texto += '<Town>' + address.city[:50] + '</Town>'
                else:
                    log.add(_('User error:\n\nPartner %s has no city.') %
                            address.name, True)
                    raise log
                if address.state_id.name:
                    texto += '<Province>' + address.state_id.name[:20] +\
                             '</Province>'
                else:
                    log.add(_('User error:\n\nPartner %s has no province.') %
                            address.name, True)
                    raise log
                if address.country_id.code_3166:
                    texto += '<CountryCode>' + address.country_id.code_3166 +\
                             '</CountryCode>'
                else:
                    log.add(_('User error:\n\nPartner %s has no country.') %
                            address.name, True)
                    raise log
                texto += '</AddressInSpain>'

                texto += '<ContactDetails>'
                if address.phone:
                    texto += '<Telephone>' +\
                             address.phone[:15] +\
                             '</Telephone>'
                if address.fax:
                    texto += '<TeleFax>' + address.fax[:15] + '</TeleFax>'
                if address.website:
                    texto += '<WebAddress>' + address.website[:60] + '</WebAddress>'
                if address.email:
                    texto += '<ElectronicMail>' + address.email[:60] +\
                             '</ElectronicMail>'
                if address.name:
                    texto += '<ContactPersons>' + address.name[:40] +\
                             '</ContactPersons>'
                texto += '</ContactDetails>'

                if administrative:
                    texto += "</AdministrativeCentre>"

                return texto

            if administrative:
                # Oficina contable
                texto += create_administrative_centres(
                    invoice_partner_address_obj, "01")
                # Órgano Gestor
                texto += create_administrative_centres(
                    contact_partner_address_obj or
                    invoice_partner_address_obj, "02")
                # Unidad tramitadora
                texto += create_administrative_centres(
                    invoice_partner_address_obj, "03")
                # Órgano proponente
                if invoice_partner_address_obj.organo_proponente:
                    texto += create_administrative_centres(
                        invoice_partner_address_obj, "04")
                texto += "</AdministrativeCentres>"

            if tipo_buyer == 'F':
                texto += '<Individual>'
                texto += '<Name>' + invoice_partner_obj.name + '</Name>'
                texto += '<FirstSurname></FirstSurname>'
                texto += '<SecondSurname></SecondSurname>'
            else:
                texto += '<LegalEntity>'
                texto += '<CorporateName>' + invoice_partner_obj.name +\
                         '</CorporateName>'

            administrative = False
            texto += create_administrative_centres(
                invoice_partner_obj, "00")

            if tipo_buyer == 'F':
                texto += '</Individual>'
            else:
                texto += '</LegalEntity>'
            texto += '</BuyerParty>'
            texto += '</Parties>'
            return texto

        def _taxes_output():
            texto = ''
            taxes_withhel = 0.0

            texto += '<TaxesOutputs>'

            for l in invoice.tax_line:
                taxes_withhel += l.base_amount
                texto += '<Tax>'
                texto += '<TaxTypeCode>01</TaxTypeCode>'
                if l.tax_code_id:
                    taxes = self.env["account.tax"].\
                        search([("tax_code_id", "=", l.tax_code_id.id)])
                    amount = abs(taxes[0].amount)
                else:
                    amount = 0
                texto += '<TaxRate>' + str('%.2f' % (amount * 100)) +\
                         '</TaxRate>'
                texto += '<TaxableBase>'
                texto += '<TotalAmount>' + str('%.2f' % l.base_amount) +\
                         '</TotalAmount>'
                texto += '</TaxableBase>'
                texto += '<TaxAmount>'
                texto += '<TotalAmount>' + str('%.2f' % l.tax_amount) +\
                         '</TotalAmount>'
                texto += '</TaxAmount>'
                texto += '</Tax>'

            texto += '</TaxesOutputs>'

            return texto

        def _invoice_totals():

            total_gross_amount = 0.0
            texto = ''

            for line in invoice.invoice_line:
                total_gross_amount += line.price_subtotal

            texto += '<InvoiceTotals>'
            texto += '<TotalGrossAmount>' + \
                     str('%.2f' % total_gross_amount) + '</TotalGrossAmount>'
            # despues descuentos cabercera pero en OpenERP no se donde estan
            # despues gastos de envio no se como aplicar si se pueden
            # si se utilizaran los anteriores aqui se le restaria descuentos
            #  y sumarian gastos
            texto += '<TotalGrossAmountBeforeTaxes>' + \
                     str('%.2f' % total_gross_amount) +\
                     '</TotalGrossAmountBeforeTaxes>'
            texto += '<TotalTaxOutputs>' + \
                     str('%.2f' % invoice.amount_tax) + '</TotalTaxOutputs>'
            texto += '<TotalTaxesWithheld>0.00</TotalTaxesWithheld>'
            texto += '<InvoiceTotal>' + \
                     str('%.2f' % invoice.amount_total) + '</InvoiceTotal>'
            # aqui se descontaria los pagos realizados a cuenta
            texto += '<TotalOutstandingAmount>' + \
                     str('%.2f' % invoice.amount_total) +\
                     '</TotalOutstandingAmount>'
            texto += '<TotalExecutableAmount>' + \
                     str('%.2f' % invoice.amount_total) +\
                     '</TotalExecutableAmount>'

            texto += '</InvoiceTotals>'
            return texto

        def _invoice_items():

            rate = 0.0
            texto = ''
            texto += '<Items>'

            for line in invoice.invoice_line:
                texto += '<InvoiceLine>'
                texto += '<ItemDescription>' + line.name + '</ItemDescription>'
                texto += '<Quantity>' + str(line.quantity) + '</Quantity>'
                texto += '<UnitPriceWithoutTax>'
                texto += str('%.6f' % line.price_unit)
                texto += '</UnitPriceWithoutTax>'
                texto += '<TotalCost>' +\
                         str('%.6f' % (line.quantity * line.price_unit)) +\
                         '</TotalCost>'
                texto += '<DiscountsAndRebates>'
                texto += '<Discount>'
                texto += '<DiscountReason>Descuento</DiscountReason>'
                texto += '<DiscountRate>' +\
                         str('%.4f' % line.discount) + '</DiscountRate>'
                texto += '<DiscountAmount>'
                texto += str('%.6f' % (
                    (line.price_unit*line.quantity) - line.price_subtotal))
                texto += '</DiscountAmount>'
                texto += '</Discount>'
                texto += '</DiscountsAndRebates>'
                texto += '<GrossAmount>' + \
                         str('%.6f' % line.price_subtotal) + '</GrossAmount>'
                texto += '<TaxesOutputs>'
                for l in line.invoice_line_tax_id:
                    rate = '%.2f' % (l.amount * 100)
                    texto += '<Tax>'
                    texto += '<TaxTypeCode>01</TaxTypeCode>'
                    texto += '<TaxRate>' + str(rate) + '</TaxRate>'
                    texto += '<TaxableBase>'
                    texto += '<TotalAmount>'
                    texto += str('%.2f' % line.price_subtotal)
                    texto += '</TotalAmount>'
                    texto += '</TaxableBase>'
                    texto += '</Tax>'
                texto += '</TaxesOutputs>'
                texto += '</InvoiceLine>'

            texto += '</Items>'
            return texto

        def _invoice_payments():
            texto = ''
            texto += '<PaymentDetails>'

            # Antes de nada, obtenemos el conjunto de vencimientos.
            # Para ello, buscamos los apuntes contra la misma cuenta contable
            # definida en la factura (la cuenta de cliente).
            for move in invoice.move_id.line_id:
                # Con esto evitamos incluir las líneas que no se corresponden
                # con vencimientos.
                if move.account_id.id != invoice.account_id.id:
                    continue
                texto += '<Installment>'
                date_maturity = invoice.date_invoice
                if move.date_maturity:
                    date_maturity = move.date_maturity
                texto += '<InstallmentDueDate>' + date_maturity +\
                         '</InstallmentDueDate>'
                if move.debit > move.credit:
                    pay_amount = move.debit
                else:
                    pay_amount = -move.credit
                texto += '<InstallmentAmount>' + str('%.2f' % pay_amount) +\
                         '</InstallmentAmount>'
                # Nos aseguramos de que se ha seleccionado el tipo de pago.
                if not invoice.payment_mode_id.face_code_id:
                    log.add(_('User error:\n\nFACe code is not configured in '
                              'invoice payment mode.'), True)
                    raise log
                texto += '<PaymentMeans>' +\
                         invoice.payment_mode_id.face_code_id.code +\
                         '</PaymentMeans>'

                # En función del tipo de pago seleccionado, debemos añadir la
                # cuenta corriente de la empresa, o la cuenta corriente del
                # cliente.
                if invoice.payment_mode_id.face_code_id.code == '02':
                    if not invoice.partner_bank_id:
                        log.add(_('User error:\n\nYou must select a bank'
                                  ' account in invoice.'), True)
                        raise log
                    texto += '<AccountToBeDebited>'
                    texto += '<IBAN>' + invoice.partner_bank_id.iban +\
                             '</IBAN>'
                    texto += '</AccountToBeDebited>'
                else:
                    texto += '<AccountToBeCredited>'
                    texto += '<IBAN>' +\
                             invoice.payment_mode_id.bank_id.iban + '</IBAN>'
                    texto += '</AccountToBeCredited>'
                texto += '</Installment>'

            texto += '</PaymentDetails>'
            return texto

        def _invoices_facturae():

            texto = ''
            texto += '<Invoices>'
            texto += '<Invoice>'
            texto += '<InvoiceHeader>'
            texto += '<InvoiceNumber>' + invoice.number + '</InvoiceNumber>'
            texto += '<InvoiceSeriesCode></InvoiceSeriesCode>'
            texto += '<InvoiceDocumentType>FC</InvoiceDocumentType>'
            texto += '<InvoiceClass>OO</InvoiceClass>'
            texto += '</InvoiceHeader>'
            texto += '<InvoiceIssueData>'
            texto += '<IssueDate>' + invoice.date_invoice + '</IssueDate>'
            texto += '<InvoiceCurrencyCode>' + invoice.currency_id.name +\
                     '</InvoiceCurrencyCode>'
            texto += '<TaxCurrencyCode>' + invoice.currency_id.name +\
                     '</TaxCurrencyCode>'
            texto += '<LanguageName>es</LanguageName>'
            texto += '</InvoiceIssueData>'
            texto += _taxes_output()
            texto += _invoice_totals()
            texto += _invoice_items()
            if invoice.payment_mode_id:
                texto += _invoice_payments()
            texto += '<AdditionalData>'
            texto += '<InvoiceAdditionalInformation>'
            texto += (invoice.comment or "")
            texto += '</InvoiceAdditionalInformation>'
            texto += '</AdditionalData>'
            texto += '</Invoice>'
            texto += '</Invoices>'
            return texto

        def _end_document():
            return '</fe:Facturae>'

        def _run_java_sign(command):
            # call = [['java','-jar','temp.jar']]
            res = subprocess.call(command, stdout=None, stderr=None)
            if res > 0:
                log.add(_("Warning - result was %d" % res))
            return res

        def _sign_document():
            path = os.path.realpath(os.path.dirname(__file__))
            path += '/../java/'
            # Almacenamos nuestra cadena XML en un fichero y
            # creamos los ficheros auxiliares.
            file_name_unsigned = path + 'unsigned_' + file_name
            file_name_signed = path + file_name
            file_unsigned = open(file_name_unsigned, "w+")
            file_unsigned.write(xml_facturae)
            file_unsigned.close()
            file_signed = open(file_name_signed, "w+")

            # Extraemos los datos del certificado para la firma electrónica.
            certificate = invoice.company_id.facturae_cert
            cert_passwd = invoice.company_id.facturae_cert_password
            cert_path = path + 'certificado.pfx'
            cert_file = open(cert_path, 'wb')
            cert_file.write(certificate.decode('base64'))
            cert_file.close()

            # Componemos la llamada al firmador.
            call = ['java', '-jar', path + 'FacturaeJ.jar', '0']
            call += [file_name_unsigned, file_name_signed]
            call += ['facturae31']
            call += [cert_path, cert_passwd]
            _run_java_sign(call)

            # Cerramos y eliminamos ficheros temporales.
            file_content = file_signed.read()
            file_signed.close()
            os.remove(file_name_unsigned)
            os.remove(file_name_signed)
            os.remove(cert_path)

            return file_content

        xml_facturae = ''
        log = Log()
        invoice_ids = self.env.context.get('active_ids', [])
        if not invoice_ids or len(invoice_ids) > 1:
            raise exceptions.\
                Warning(_('Only can select one invoice to export'))

        invoice = self.env['account.invoice'].browse(invoice_ids[0])
        # contador = 1
        # lines_issued = []
        xml_facturae += _format_xml()
        xml_facturae += _header_facturae()
        xml_facturae += _parties_facturae()
        xml_facturae += _invoices_facturae()
        xml_facturae += _end_document()
        xml_facturae = unidecode(unicode(xml_facturae))
        xml_facturae = self.end_document_hook(xml_facturae)
        if invoice.company_id.facturae_cert and self.firmar_facturae:
            file_name = (_(
                'facturae') + '_' + invoice.number + '.xsig').replace('/', '-')
            invoice_file = _sign_document()
        else:
            invoice_file = xml_facturae
            file_name = (_(
                'facturae') + '_' + invoice.number + '.xml').replace('/', '-')

        file = base64.encodestring(invoice_file)
        self.env['ir.attachment'].create({'name': file_name,
                                          'datas': file,
                                          'datas_fname': file_name,
                                          'res_model': 'account.invoice',
                                          'res_id': invoice.id})

        log.add(_("Export successful\n\nSummary:\nInvoice number: %s\n") %
                invoice.number)

        self.write({'note': log(),
                    'facturae': file,
                    'facturae_fname': file_name,
                    'state': 'second'})

        return {'type': 'ir.actions.act_window',
                'res_model': 'create.facturae',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': self.id,
                'views': [(False, 'form')],
                'target': 'new'}
