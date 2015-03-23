# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Alejandro Sanchez (http://www.asr-oss.com) All Rights Reserved.
#                       Alejandro Sanchez <alejandro@asr-oss.com>
#    Copyright (c) 2015 Omar Castiñeira Saavedra (http://www.pexego.es)
#    Copyright (c) 2015 Factor Libre (http://www.factorlibre.com)
#                       Ismael Calvo <ismael.calvo@factorlibre.com)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import base64
import netsvc
from tools.translate import _
from osv import osv, fields
import pooler
import wizard
import base64
import subprocess
import os
import sys

logger = netsvc.Logger()


def conv_ascii(text):
    """Convierte vocales accentuadas, ñ y ç a sus caracteres equivalentes ASCII"""
    old_chars = ['á','é','í','ó','ú','à','è','ì','ò','ù','ä','ë','ï','ö','ü','â','ê','î','ô','û','Á','É','Í','Ú','Ó','À','È','Ì','Ò','Ù','Ä','Ë','Ï','Ö','Ü','Â','Ê','Î','Ô','Û','ñ','Ñ','ç','Ç','ª','º']
    new_chars = ['a','e','i','o','u','a','e','i','o','u','a','e','i','o','u','a','e','i','o','u','A','E','I','O','U','A','E','I','O','U','A','E','I','O','U','A','E','I','O','U','n','N','c','C','a','o']
    for old, new in zip(old_chars, new_chars):
        text = text.replace(unicode(old,'UTF-8'), new)
    return text

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

class create_facturae(osv.osv_memory):

    _name = "create.facturae"

    _columns = {
        'facturae' : fields.binary('Factura-E file', readonly=True),
        'facturae_fname': fields.char("File name", size=64),
        'note': fields.text('Log'),
        'state': fields.selection([('first', 'First'),('second','Second')], 'State', readonly=True)
    }

    _defaults = {
        'state': 'first'
    }

    def create_facturae_file(self, cr, uid, ids, context):

        def _format_xml():
            #formato y definicion del fichero xml
            texto = '﻿<?xml version="1.0" encoding="UTF-8"?>'
            texto = '<fe:Facturae xmlns:fe="http://www.facturae.es/Facturae/2009/v3.2/Facturae" xmlns:ds="http://www.w3.org/2000/09/xmldsig#">'
            return texto

        def _persona(vat):
            texto = ''
            if vat[2:3].isdigit() == True:
                texto = 'F'
            else:
                texto = 'J'
            return texto

        def _apoyo_batch():

            texto = ''
            currency = invoice.currency_id

            texto += '<TotalInvoicesAmount>'
            texto += '<TotalAmount>' + str('%.2f' % invoice.amount_total) + '</TotalAmount>'
            texto += '</TotalInvoicesAmount>'

            texto += '<TotalOutstandingAmount>'
            texto += '<TotalAmount>' + str('%.2f' % invoice.amount_total) + '</TotalAmount>'
            texto += '</TotalOutstandingAmount>'

            texto += '<TotalExecutableAmount>'
            texto += '<TotalAmount>' + str('%.2f' % invoice.amount_total) + '</TotalAmount>'
            texto += '</TotalExecutableAmount>'
            texto += '<InvoiceCurrencyCode>' + currency.name + '</InvoiceCurrencyCode>'

            return texto

        def _header_facturae(cr, context):

            company_partner_obj = invoice.company_id.partner_id

            schemaversion = '3.2'
            modality = 'I'

            if not invoice.number:
                log.add(_('User error:\n\nCan not create Factura-E file if invoice has no number.'))
                raise log

            if company_partner_obj.vat:
                BatchIdentifier = invoice.number + company_partner_obj.vat
            else:
                log.add(_('User error:\n\nCompany %s has no VAT number.') % (company_partner_obj.name), True)
                raise log

            texto = ''
            texto += '<FileHeader>'
            texto += '<SchemaVersion>' + schemaversion + '</SchemaVersion>'
            texto += '<Modality>' + modality + '</Modality>'
            texto += '<InvoiceIssuerType>EM</InvoiceIssuerType>'
            texto += '<Batch>'
            texto += '<BatchIdentifier>' + BatchIdentifier + '</BatchIdentifier>'
            texto += '<InvoicesCount>1</InvoicesCount>'
            texto += _apoyo_batch()
            texto += '</Batch>'
            texto += '</FileHeader>'
            return texto

        def _parties_facturae(cr, context):

            company_obj = invoice.company_id
            company_partner_obj = company_obj.partner_id
            invoice_partner_obj = invoice.partner_id
            invoice_partner_address_obj = invoice.address_invoice_id
            contact_partner_address_obj = invoice.address_contact_id

            #obtencion direccion company recogemos la de facura adress_get si no encuentra invoice devuelve primera
            company_address_id = self.pool.get('res.partner').address_get(cr, uid, [company_obj.partner_id.id], ['invoice'])
            if not company_address_id['invoice']:
                log.add(_('User error:\n\nCompany %s does not have an invoicing address.') % (company_partner_obj.name))
                raise log
            company_address_obj = self.pool.get('res.partner.address').browse(cr, uid, company_address_id['invoice'])

            #obtencion de la direccion del partner
            partner_address_invoice = invoice.address_invoice_id

            tipo_seller = _persona(company_partner_obj.vat)

            if invoice_partner_obj.vat:
                tipo_buyer = _persona(invoice_partner_obj.vat)
            else:
                log.add(_('User error:\n\nPartner %s does not have a VAT number.') % (invoice_partner_obj.name), True)
                raise log

            texto = ''
            texto += '<Parties>'
            texto += '<SellerParty>'
            texto += '<TaxIdentification>'
            texto += '<PersonTypeCode>' + tipo_seller + '</PersonTypeCode>'
            texto += '<ResidenceTypeCode>U</ResidenceTypeCode>'
            texto += '<TaxIdentificationNumber>' + company_partner_obj.vat + '</TaxIdentificationNumber>'
            texto += '</TaxIdentification>'

            if tipo_seller == 'F':
                texto += '<Individual>'
                texto += '<Name>' + invoice_partner_obj.name + '</Name>'
                texto += '<FirstSurname></FirstSurname>'
                texto += '<SecondSurname></SecondSurname>'
            else:
                texto += '<LegalEntity>'
                texto += '<CorporateName>' + company_obj.name + '</CorporateName>'
                texto += '<TradeName>' + company_obj.name + '</TradeName>'

            #Fijo hasta que se tome una decision no son obligatorios
            #texto += '<RegistrationData>'
            #texto += '<Book>1</Book>'
            #texto += '<RegisterOfCompaniesLocation>12AP22</RegisterOfCompaniesLocation>'
            #texto += '<Sheet>3</Sheet>'
            #texto += '<Folio>15</Folio>'
            #texto += '<Section>2</Section>'
            #texto += '<Volume>12</Volume>'
            #texto += '<AdditionalRegistrationData>Sin datos</AdditionalRegistrationData>'
            #texto += '</RegistrationData>'
            #fin
            texto += '<AddressInSpain>'
            if company_address_obj.street:
                if company_address_obj.street2:
                    texto += '<Address>' + company_address_obj.street + ' ' + company_address_obj.street2 + '</Address>'
                else:
                    texto += '<Address>' + company_address_obj.street + '</Address>'
            else:
                log.add(_('User error:\n\nCompany %s has no street.') % (company_partner_obj.name), True)
                raise log
            if company_address_obj.zip:
                texto += '<PostCode>' + company_address_obj.zip + '</PostCode>'
            else:
                log.add(_('User error:\n\nCompany %s has no zip code.') % (company_partner_obj.name), True)
                raise log
            if company_address_obj.city:
                texto += '<Town>' + company_address_obj.city + '</Town>'
            else:
                log.add(_('User error:\n\nCompany %s has no city.') % (company_partner_obj.name), True)
                raise log
            if  company_address_obj.state_id.name:
                texto += '<Province>' + company_address_obj.state_id.name + '</Province>'
            else:
                log.add(_('User error:\n\nCompany %s has no province.') % (company_partner_obj.name), True)
                raise log
            if company_address_obj.country_id.code_3166:
                texto += '<CountryCode>' + company_address_obj.country_id.code_3166 + '</CountryCode>'
            else:
                log.add(_('User error:\n\nCompany %s has no country.') % (company_partner_obj.name), True)
                raise log
            texto += '</AddressInSpain>'

            texto += '<ContactDetails>'
            if company_address_obj.phone:
                texto += '<Telephone>' + company_address_obj.phone + '</Telephone>'
            if company_address_obj.fax:
                texto += '<TeleFax>' + company_address_obj.fax + '</TeleFax>'
            if company_partner_obj.website:
                texto += '<WebAddress>' + company_partner_obj.website + '</WebAddress>'
            if company_address_obj.email:
                texto += '<ElectronicMail>' + company_address_obj.email + '</ElectronicMail>'
            if company_address_obj.name:
                texto += '<ContactPersons>' + company_address_obj.name + '</ContactPersons>'
            texto += '</ContactDetails>'

            if tipo_seller == 'F':
                texto += '</Individual>'
            else:
                texto += '</LegalEntity>'

            texto += '</SellerParty>'
            texto += '<BuyerParty>'
            texto += '<TaxIdentification>'
            texto += '<PersonTypeCode>' + tipo_buyer + '</PersonTypeCode>'
            texto += '<ResidenceTypeCode>U</ResidenceTypeCode>'
            texto += '<TaxIdentificationNumber>' + invoice_partner_obj.vat + '</TaxIdentificationNumber>'
            texto += '</TaxIdentification>'



            administrative = False
            if invoice_partner_address_obj.facturae:
                texto += "<AdministrativeCentres>"
                administrative = True

            def create_administrative_centres(address, code):
                texto = ""
                if administrative:
                    texto += "<AdministrativeCentre>"
                    if code == '01':
                        texto += "<CentreCode>" + address.oficina_contable + "</CentreCode>"
                    elif code == '02':
                        texto += "<CentreCode>" + address.organo_gestor + "</CentreCode>"
                    elif code == '03':
                        texto += "<CentreCode>" + address.unidad_tramitadora + "</CentreCode>"
                    else:
                        texto += "<CentreCode></CentreCode>"
                    texto += "<RoleTypeCode>" + code + "</RoleTypeCode>"

                texto += '<AddressInSpain>'
                if address.street:
                    if address.street2:
                        texto += '<Address>' + address.street + ' ' + address.street2 + '</Address>'
                    else:
                        texto += '<Address>' + address.street + '</Address>'
                else:
                    log.add(_('User error:\n\nPartner %s has no street.') % (address.name), True)
                    raise log
                if address.zip:
                    texto += '<PostCode>' + address.zip + '</PostCode>'
                else:
                    log.add(_('User error:\n\nPartner %s has no zip code.') % (address.name), True)
                    raise log

                if address.city:
                    texto += '<Town>' + address.city + '</Town>'
                else:
                    log.add(_('User error:\n\nPartner %s has no city.') % (address.name), True)
                    raise log
                if address.state_id.name:
                    texto += '<Province>' + address.state_id.name + '</Province>'
                else:
                    log.add(_('User error:\n\nPartner %s has no province.') % (address.name), True)
                    raise log
                if address.country_id.code_3166:
                    texto += '<CountryCode>' + address.country_id.code_3166 + '</CountryCode>'
                else:
                    log.add(_('User error:\n\nPartner %s has no country.') % (address.name), True)
                    raise log
                texto += '</AddressInSpain>'

                texto += '<ContactDetails>'
                if address.phone:
                    texto += '<Telephone>' + address.phone + '</Telephone>'
                if address.fax:
                    texto += '<TeleFax>' + address.fax + '</TeleFax>'
                if address.partner_id.website:
                    texto += '<WebAddress>' + address.website + '</WebAddress>'
                if address.email:
                    texto += '<ElectronicMail>' + address.email + '</ElectronicMail>'
                if address.name:
                    texto += '<ContactPersons>' + address.name + '</ContactPersons>'
                texto += '</ContactDetails>'

                if administrative:
                    texto += "</AdministrativeCentre>"

                return texto

            if administrative:
                texto += create_administrative_centres(invoice_partner_address_obj, "01") # Oficina contable
                texto += create_administrative_centres(contact_partner_address_obj or invoice_partner_address_obj, "02") # Órgano Gestor
                texto += create_administrative_centres(invoice_partner_address_obj, "03") # Unidad tramitadora
                texto += create_administrative_centres(contact_partner_address_obj or invoice_partner_address_obj, "04") # Órgano proponente
                texto += "</AdministrativeCentres>"

            if tipo_buyer == 'F':
                texto += '<Individual>'
                texto += '<Name>' + invoice_partner_obj.name + '</Name>'
                texto += '<FirstSurname></FirstSurname>'
                texto += '<SecondSurname></SecondSurname>'
            else:
                texto += '<LegalEntity>'
                texto += '<CorporateName>' + invoice_partner_obj.name + '</CorporateName>'

            administrative = False
            texto += create_administrative_centres(invoice_partner_address_obj, "00")

            if tipo_buyer == 'F':
                texto += '</Individual>'
            else:
                texto += '</LegalEntity>'
            texto += '</BuyerParty>'
            texto += '</Parties>'
            return texto

        def _taxes_output():

            texto = ''
            rate = 0.0
            taxes_withhel = 0.0

            texto += '<TaxesOutputs>'

            for l in invoice.tax_line:
                taxes_withhel += l.base_amount
                texto += '<Tax>'
                texto += '<TaxTypeCode>01</TaxTypeCode>'
                if l.tax_code_id:
                    cr.execute('SELECT t.amount FROM account_tax t WHERE t.tax_code_id =%s',(l.tax_code_id.id,))
                else:
                    raise osv.except_osv(_('Error !'), _('The tax line "%s" has no tax code' % l.name))
                res = cr.fetchone()
                texto += '<TaxRate>' + str('%.2f' % (abs(res[0]) * 100)) + '</TaxRate>'
                texto += '<TaxableBase>'
                texto += '<TotalAmount>' + str('%.2f' % l.base_amount) + '</TotalAmount>'
                texto += '</TaxableBase>'
                texto += '<TaxAmount>'
                texto += '<TotalAmount>' + str('%.2f' % l.tax_amount) + '</TotalAmount>'
                texto += '</TaxAmount>'
                texto += '</Tax>'

            texto += '</TaxesOutputs>'

            texto += '<TaxesWithheld>'
            texto += '<Tax>'
            texto += '<TaxTypeCode>01</TaxTypeCode>'
            texto += '<TaxRate>0.00</TaxRate>'
            texto += '<TaxableBase>'
            texto += '<TotalAmount>0.00</TotalAmount>'
            texto += '</TaxableBase>'
            texto += '<TaxAmount>'
            texto += '<TotalAmount>0.00</TotalAmount>'
            texto += '</TaxAmount>'
            texto += '</Tax>'
            texto += '</TaxesWithheld>'

            return texto

        def _invoice_totals():

            total_gross_amount = 0.0
            texto = ''

            for line in invoice.invoice_line:
                total_gross_amount += line.price_subtotal

            texto += '<InvoiceTotals>'
            texto += '<TotalGrossAmount>' + str('%.2f' % total_gross_amount) + '</TotalGrossAmount>'
            #despues descuentos cabercera pero en OpenERP no se donde estan
            #despues gastos de envio no se como aplicar si se pueden
            #si se utilizaran los anteriores aqui se le restaria descuentos y sumarian gastos
            texto += '<TotalGrossAmountBeforeTaxes>' + str('%.2f' % total_gross_amount) + '</TotalGrossAmountBeforeTaxes>'
            texto += '<TotalTaxOutputs>' + str('%.2f' % invoice.amount_tax) + '</TotalTaxOutputs>'
            texto += '<TotalTaxesWithheld>0.00</TotalTaxesWithheld>'
            texto += '<InvoiceTotal>' + str('%.2f' % invoice.amount_total) + '</InvoiceTotal>'
            #aqui se descontaria los pagos realizados a cuenta
            texto += '<TotalOutstandingAmount>' + str('%.2f' % invoice.amount_total) + '</TotalOutstandingAmount>'
            texto += '<TotalExecutableAmount>' + str('%.2f' % invoice.amount_total) + '</TotalExecutableAmount>'

            texto += '</InvoiceTotals>'
            return texto

        def _invoice_items():

            rate = 0.0
            texto = ''
            texto += '<Items>'

            for line in invoice.invoice_line:
                if line.invoice_line_tax_id and line.invoice_line_tax_id[0].price_include:
                    tax_amount = line.invoice_line_tax_id[0].amount
                    price_unit = line.price_unit/(1+tax_amount)
                    if line.discount:
                        discount_amount = price_unit * line.quantity - line.price_subtotal
                    else:
                        discount_amount = 0.0
                else:
                    price_unit = line.price_unit
                    discount_amount = line.price_unit * line.quantity - line.price_subtotal
                texto += '<InvoiceLine>'
                texto += '<ItemDescription>' + line.name + '</ItemDescription>'
                texto += '<Quantity>' + str(line.quantity) + '</Quantity>'
                texto += '<UnitPriceWithoutTax>' + str('%.6f' % price_unit) + '</UnitPriceWithoutTax>'
                texto += '<TotalCost>' + str('%.6f' % (line.quantity * price_unit)) + '</TotalCost>'
                texto += '<DiscountsAndRebates>'
                texto += '<Discount>'
                texto += '<DiscountReason>Descuento</DiscountReason>'
                texto += '<DiscountRate>' + str('%.4f' % line.discount) + '</DiscountRate>'
                texto += '<DiscountAmount>' + str('%.6f' % discount_amount) + '</DiscountAmount>'
                texto += '</Discount>'
                texto += '</DiscountsAndRebates>'
                texto += '<GrossAmount>' + str('%.6f' % line.price_subtotal) + '</GrossAmount>'
                texto += '<TaxesWithheld>'
                texto += '<Tax>'
                texto += '<TaxTypeCode>01</TaxTypeCode>'
                texto += '<TaxRate>0.00</TaxRate>'
                texto += '<TaxableBase>'
                texto += '<TotalAmount>0.00</TotalAmount>'
                texto += '</TaxableBase>'
                texto += '</Tax>'
                texto += '</TaxesWithheld>'
                texto += '<TaxesOutputs>'
                for l in line.invoice_line_tax_id:
                    rate = '%.2f' % (l.amount * 100)
                    texto += '<Tax>'
                    texto += '<TaxTypeCode>01</TaxTypeCode>'
                    texto += '<TaxRate>' + str(rate) + '</TaxRate>'
                    texto += '<TaxableBase>'
                    texto += '<TotalAmount>' + str('%.2f' % line.price_subtotal) + '</TotalAmount>'
                    texto += '</TaxableBase>'
                    texto += '</Tax>'
                texto += '</TaxesOutputs>'
                texto += '</InvoiceLine>'

            texto += '</Items>'
            return texto

        def _invoices_facturae():

            texto = ''
            texto += '<Invoices>'
            texto += '<Invoice>'
            texto += '<InvoiceHeader>'
            texto += '<InvoiceNumber>' + invoice.number + '</InvoiceNumber>'
            texto += '<InvoiceSeriesCode>' + invoice.number + '</InvoiceSeriesCode>'
            texto += '<InvoiceDocumentType>FC</InvoiceDocumentType>'
            texto += '<InvoiceClass>OO</InvoiceClass>'
            texto += '</InvoiceHeader>'
            texto += '<InvoiceIssueData>'
            texto += '<IssueDate>' + invoice.date_invoice + '</IssueDate>'
            texto += '<InvoiceCurrencyCode>' + invoice.currency_id.name + '</InvoiceCurrencyCode>'
            texto += '<TaxCurrencyCode>' + invoice.currency_id.name + '</TaxCurrencyCode>'
            texto += '<LanguageName>es</LanguageName>'
            texto += '</InvoiceIssueData>'
            texto += _taxes_output()
            texto += _invoice_totals()
            texto += _invoice_items()
            texto += '<AdditionalData>'
            texto += '<InvoiceAdditionalInformation>' + (invoice.comment or "") + '</InvoiceAdditionalInformation>'
            texto += '</AdditionalData>'
            texto += '</Invoice>'
            texto += '</Invoices>'
            return texto

        def _end_document():
            return '</fe:Facturae>'

        def _run_java_sign(command):
            #call = [['java','-jar','temp.jar']]
            res = subprocess.call(command,stdout=None,stderr=None)
            if res > 0 :
                print "Warning - result was %d" % res
            return res

        def _sign_document(xml_facturae,file_name,invoice):
            path = os.path.realpath(os.path.dirname(__file__))
            path += '/../java/'
            # Almacenamos nuestra cadena XML en un fichero y creamos los ficheros auxiliares.
            file_name_unsigned = path + 'unsigned_' + file_name
            file_name_signed = path + file_name
            file_unsigned = open(file_name_unsigned,"w+")
            file_unsigned.write(xml_facturae.encode('ascii', 'replace'))
            file_unsigned.close()
            file_signed = open(file_name_signed,"w+")

            # Extraemos los datos del certificado para la firma electrónica.
            certificate = invoice.company_id.facturae_cert
            cert_passwd = invoice.company_id.facturae_cert_password
            cert_path = path + 'certificado.pfx'
            cert_file = open(cert_path,'wb')
            cert_file.write(certificate.decode('base64'))
            cert_file.close()

            # Componemos la llamada al firmador.
            call = ['java','-jar',path + 'FacturaeJ.jar','0']
            call += [file_name_unsigned,file_name_signed]
            call += ['facturae31']
            call += [cert_path,cert_passwd]
            res = _run_java_sign(call)

            # Cerramos y eliminamos ficheros temporales.
            file_content = file_signed.read()
            file_signed.close()
            os.remove(file_name_unsigned)
            os.remove(file_name_signed)
            os.remove(cert_path)

            return file_content

        xml_facturae = ''
        log = Log()
        obj = self.browse(cr, uid, ids[0])
        invoice_ids = context.get('active_ids', [])
        if not invoice_ids or len(invoice_ids) > 1:
            raise osv.except_osv(_('Error !'), _('Only can select one invoice to export'))

        invoice = self.pool.get('account.invoice').browse(cr, uid, invoice_ids[0], context)
        contador = 1
        lines_issued = []
        xml_facturae += _format_xml()
        xml_facturae += _header_facturae(cr, context)
        xml_facturae += _parties_facturae(cr, context)
        xml_facturae += _invoices_facturae()
        xml_facturae += _end_document()
        xml_facturae = conv_ascii(xml_facturae)
        if invoice.company_id.facturae_cert:
            file_name = (_('facturae') + '_' + invoice.number + '.xsig').replace('/','-')
            invoice_file = _sign_document(xml_facturae,file_name,invoice)
        else:
            invoice_file = xml_facturae
            file_name = (_('facturae') + '_' + invoice.number + '.xml').replace('/','-')

        file = base64.encodestring(invoice_file)
        self.pool.get('ir.attachment').create(cr, uid, {
            'name': file_name,
            'datas': file,
            'datas_fname': file_name,
            'res_model': 'account.invoice',
            'res_id': invoice.id,
            }, context=context)
        log.add(_("Export successful\n\nSummary:\nInvoice number: %s\n") % (invoice.number))

        obj.write({'note': log(),
                   'facturae': file,
                   'facturae_fname': file_name,
                   'state': 'second'})
        return True


create_facturae()
