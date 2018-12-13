# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import re
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    total_amount = fields.Float(
        compute='_compute_total_amount', store=True, readonly=True)

    @api.multi
    @api.depends(
        'payment_line_ids', 'payment_line_ids.amount_currency')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_company_currency = sum(
                rec.mapped('payment_line_ids.amount_currency') or
                [0.0])

    def to_ascii(self, text):
        """Converts special characters such as those with accents to their
        ASCII equivalents"""
        old_chars = ['á', 'é', 'í', 'ó', 'ú', 'à', 'è', 'ì', 'ò', 'ù', 'ä',
                     'ë', 'ï', 'ö', 'ü', 'â', 'ê', 'î', 'ô', 'û', 'Á', 'É',
                     'Í', 'Ú', 'Ó', 'À', 'È', 'Ì', 'Ò', 'Ù', 'Ä', 'Ë', 'Ï',
                     'Ö', 'Ü', 'Â', 'Ê', 'Î', 'Ô', 'Û', 'ñ', 'Ñ', 'ç', 'Ç',
                     'ª', 'º', '·', '\n']
        new_chars = ['a', 'e', 'i', 'o', 'u', 'a', 'e', 'i', 'o', 'u', 'a',
                     'e', 'i', 'o', 'u', 'a', 'e', 'i', 'o', 'u', 'A', 'E',
                     'I', 'U', 'O', 'A', 'E', 'I', 'O', 'U', 'A', 'E', 'I',
                     'O', 'U', 'A', 'E', 'I', 'O', 'U', 'n', 'N', 'c', 'C',
                     'a', 'o', '.', ' ']
        for old, new in zip(old_chars, new_chars):
            text = text.replace(old, new)
        return text

    def convert_text(self, text, size, justified='left'):
        if justified == 'left':
            return self.to_ascii(text)[:size].ljust(size)
        else:
            return self.to_ascii(text)[:size].rjust(size)

    def convert_float(self, number, size):
        text = str(int(round(number * 100, 0)))
        if len(text) > size:
            raise UserError(
                _('Error:\n\nCan not convert float number %(number).2f '
                  'to fit in %(size)d characters.') % {
                    'number': number,
                    'size': size
                    })
        return text.zfill(size)

    def convert_int(self, number, size):
        text = str(number)
        if len(text) > size:
            raise UserError(
                _('Error:\n\nCan not convert integer number %(number)d '
                  'to fit in %(size)d characters.') % {
                    'number': number,
                    'size': size
                    })
        return text.zfill(size)

    def convert(self, value, size, justified='left'):
        if not value:
            return self.convert_text('', size)
        elif isinstance(value, float):
            return self.convert_float(value, size)
        elif isinstance(value, int):
            return self.convert_int(value, size)
        else:
            return self.convert_text(value, size, justified)

    def convert_vat(self, partner):
        # Copied from mod349
        if partner.country_id.code:
            country_pattern = "%s|%s.*" % (partner.country_id.code,
                                           partner.country_id.code.lower())
            vat_regex = re.compile(country_pattern, re.UNICODE | re.X)
            if partner.vat and vat_regex.match(partner.vat):
                return partner.vat[2:]
        return partner.vat
