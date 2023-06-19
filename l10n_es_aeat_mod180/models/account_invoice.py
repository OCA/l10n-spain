# -*- encoding: utf-8 -*-

from odoo import _, api, fields, models
from lxml import etree

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    informacion_catastral_id = fields.Many2one('informacion.catastral')


    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        """The purpose of this is to write a context on "order_line" field
         respecting other contexts on this field.
         There is a PR (https://github.com/odoo/odoo/pull/26607) to odoo for
         avoiding this. If merged, remove this method and add the attribute
         in the field.
         """
        res = super(AccountInvoice, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu,
        )
        if view_type == 'form':
            order_xml = etree.XML(res['arch'])
            invoice_line_fields = order_xml.xpath("//field[@name='invoice_line_ids']")
            if invoice_line_fields:
                invoice_line_field = invoice_line_fields[0]
                context = invoice_line_field.attrib.get("context", "{}").replace(
                    "{", "{'default_invoice_partner_id': partner_id, ", 1,
                )
                invoice_line_field.attrib['context'] = context
                res['arch'] = etree.tostring(order_xml)
        return res

    @api.model
    def invoice_line_move_line_get(self):
        res = super().invoice_line_move_line_get()
        invoice_line_obj = self.env['account.invoice.line']
        for vals in res:
            if vals.get('invl_id'):
                invline = invoice_line_obj.browse(vals['invl_id'])
                if invline.informacion_catastral_id:
                    vals['informacion_catastral_id'] = invline.informacion_catastral_id.id
        return res


    def _prepare_tax_line_vals(self, line, tax):
        res = super(AccountInvoice, self)._prepare_tax_line_vals(line, tax)
        if line.informacion_catastral_id:
            res.update({'informacion_catastral_id': line.informacion_catastral_id.id})
        return res

    @api.model
    def tax_line_move_line_get(self):
        res = super(AccountInvoice, self).tax_line_move_line_get()
        for tax_line in sorted(self.tax_line_ids, key=lambda x: -x.sequence):
            if tax_line.informacion_catastral_id:
                for dict in res:
                    if dict.get('invoice_tax_line_id', 0) == tax_line.id:
                        dict.update({'informacion_catastral_id': tax_line.informacion_catastral_id.id})
                        break
        return res

    @api.model
    def line_get_convert(self, line, part):
        res = super().line_get_convert(line, part)
        if line.get('informacion_catastral_id'):
            res['informacion_catastral_id'] = line['informacion_catastral_id']
        return res

