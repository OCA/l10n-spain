# -*- encoding: utf-8 -*-

from odoo import _, api, fields, models
from lxml import etree

class AccountMove(models.Model):
    _inherit = 'account.move'

    informacion_catastral_id = fields.Many2one('informacion.catastral')


    def fields_view_get(self, view_id=None, submenu=False):
        """The purpose of this is to write a context on "order_line" field
         respecting other contexts on this field.
         There is a PR (https://github.com/odoo/odoo/pull/26607) to odoo for
         avoiding this. If merged, remove this method and add the attribute
         in the field.
         """
        res = super(AccountMove, self).fields_view_get(
            view_id=view_id, submenu=submenu,
        )
        order_xml = etree.XML(res['arch'])
        move_line_fields = order_xml.xpath("//field[@name='move_line_ids']")
        if move_line_fields:
            move_line_field = move_line_fields[0]
            context = move_line_field.attrib.get("context", "{}").replace(
                "{", "{'default_move_partner_id': partner_id, ", 1,
            )
            move_line_field.attrib['context'] = context
            res['arch'] = etree.tostring(order_xml)
        return res

    def move_line_move_line_get(self):
        res = super().move_line_move_line_get()
        move_line_obj = self.env['account.move.line']
        for vals in res:
            if vals.get('invl_id'):
                invline = move_line_obj.browse(vals['invl_id'])
                if invline.informacion_catastral_id:
                    vals['informacion_catastral_id'] = invline.informacion_catastral_id.id
        return res


    def _prepare_tax_line_vals(self, line, tax):
        res = super(AccountMove, self)._prepare_tax_line_vals(line, tax)
        if line.informacion_catastral_id:
            res.update({'informacion_catastral_id': line.informacion_catastral_id.id})
        return res

    def tax_line_move_line_get(self):
        res = super(AccountMove, self).tax_line_move_line_get()
        for tax_line in sorted(self.tax_line_ids, key=lambda x: -x.sequence):
            if tax_line.informacion_catastral_id:
                for dict in res:
                    if dict.get('move_tax_line_id', 0) == tax_line.id:
                        dict.update({'informacion_catastral_id': tax_line.informacion_catastral_id.id})
                        break
        return res

    def line_get_convert(self, line, part):
        res = super().line_get_convert(line, part)
        if line.get('informacion_catastral_id'):
            res['informacion_catastral_id'] = line['informacion_catastral_id']
        return res

