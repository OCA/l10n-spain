# -*- coding: utf-8 -*-
# © 2009 Alejandro Sanchez <alejandro@asr-oss.com>
# © 2015 Ismael Calvo <ismael.calvo@factorlibre.com>
# © 2015 Tecon
# © 2015 Juanjo Algaz (MalagaTIC)
# © 2015 Omar Castiñeira (Comunitea)
# © 2016 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError
import logging
import subprocess
import os
from lxml import etree
from openerp import tools

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
    firmar_facturae = fields.Boolean(
        '¿Desea firmar digitalmente el fichero generado?',
        help='Requiere certificado en la ficha de la compañía')

    @api.model
    def _validate_facturae(self, xml_string):
        facturae_schema = etree.XMLSchema(
            etree.parse(tools.file_open(
                "Facturaev3_2.xsd", subdir="addons/l10n_es_facturae/data")))
        try:
            facturae_schema.assertValid(etree.fromstring(xml_string))
        except Exception, e:
            logger.warning(
                "The XML file is invalid against the XML Schema Definition")
            logger.warning(xml_string)
            logger.warning(e)
            raise UserError(
                _("The generated XML file is not valid against the official "
                  "XML Schema Definition. The generated XML file and the "
                  "full error have been written in the server logs. Here "
                  "is the error, which may give you an idea on the cause "
                  "of the problem : %s") % unicode(e))
        return True

    @api.multi
    def create_facturae_file(self):

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

        log = Log()
        invoice_ids = self.env.context.get('active_ids', [])
        if not invoice_ids or len(invoice_ids) > 1:
            raise UserError(_('You can only select one invoice to export'))
        invoice = self.env['account.invoice'].browse(invoice_ids[0])
        report = self.env.ref('l10n_es_facturae.report_facturae')
        xml_facturae = self.env['report'].get_html(invoice, report.report_name)
        tree = etree.fromstring(
            xml_facturae, etree.XMLParser(remove_blank_text=True))
        xml_facturae = etree.tostring(tree, pretty_print=True)
        self._validate_facturae(xml_facturae)
        if invoice.company_id.facturae_cert and self.firmar_facturae:
            file_name = (_(
                'facturae') + '_' + invoice.number + '.xsig').replace('/', '-')
            invoice_file = _sign_document()
        else:
            invoice_file = xml_facturae
            file_name = (_(
                'facturae') + '_' + invoice.number + '.xml').replace('/', '-')
        file = base64.b64encode(invoice_file)
        self.env['ir.attachment'].create({
            'name': file_name,
            'datas': file,
            'datas_fname': file_name,
            'res_model': 'account.invoice',
            'res_id': invoice.id
        })
        log.add(_("Export successful\n\nSummary:\nInvoice number: %s\n") %
                invoice.number)
        self.write({
            'note': log(),
            'facturae': file,
            'facturae_fname': file_name,
            'state': 'second'
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'create.facturae',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new'
        }
