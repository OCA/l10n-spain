# -*- coding: utf-8 -*-
# © 2009 Alejandro Sanchez <alejandro@asr-oss.com>
# © 2015 Ismael Calvo <ismael.calvo@factorlibre.com>
# © 2015 Tecon
# © 2015 Juanjo Algaz (MalagaTIC)
# © 2015 Omar Castiñeira (Comunitea)
# © 2016 Serv. Tecnol. Avanzados - Pedro M. Baeza
# © 2017 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64

from odoo import api, fields, models, _
from odoo.exceptions import Warning as UserError


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
        help='Requiere certificado en la ficha de la compañía', default=True)

    @api.multi
    def create_facturae_file(self):
        log = Log()
        invoice_ids = self.env.context.get('active_ids', [])
        if not invoice_ids or len(invoice_ids) > 1:
            raise UserError(_('You can only select one invoice to export'))
        active_model = self.env.context.get('active_model', False)
        assert active_model == 'account.invoice', \
            'Bad context propagation'
        invoice = self.env['account.invoice'].browse(invoice_ids[0])
        invoice_file, file_name = invoice.ensure_one().get_facturae(
            self.firmar_facturae)

        file = base64.b64encode(invoice_file)
        self.env['ir.attachment'].create({
            'name': file_name,
            'datas': file,
            'datas_fname': file_name,
            'res_model': 'account.invoice',
            'res_id': invoice.id,
            'mimetype': 'application/xml'
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
