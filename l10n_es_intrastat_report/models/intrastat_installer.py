# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp import tools
import csv

CN_file_year = '2017'
CN_file_delimiter = ';'


class IntrastatInstaller(models.TransientModel):
    _name = 'intrastat.installer'
    _inherit = 'res.config.installer'

    @api.model
    def _get_CN_file(self):
        return [(CN_file_year + '_en', CN_file_year + ' ' + _('English')),
                (CN_file_year + '_fr', CN_file_year + ' ' + _('French')),
                (CN_file_year + '_nl', CN_file_year + ' ' + _('Dutch'))]

    @api.model
    def _default_CN_file(self):
        lang = self.env.user.lang[:2]
        if lang not in ['fr', 'nl']:
            lang = 'en'
        return CN_file_year + '_' + lang

    CN_file = fields.Selection(
        '_get_CN_file', string='Intrastat Code File',
        required=True, default=_default_CN_file)

    @api.model
    def _load_code(self, row):
        code_obj = self.env['hs.code']
        vals = {'description': row['description']}
        cn_unit_id = row['unit_id']
        if cn_unit_id:
            cn_unit_ref = 'intrastat_product.' + cn_unit_id
            cn_unit = self.env.ref(cn_unit_ref)
            vals['intrastat_unit_id'] = cn_unit.id
        cn_code = row['code']
        cn_code_i = self.cn_lookup.get(cn_code)
        if isinstance(cn_code_i, int):
            self.cn_codes[cn_code_i].write(vals)
        else:
            vals['local_code'] = cn_code
            code_obj.create(vals)

    @api.multi
    def execute(self):
        res = super(IntrastatInstaller, self).execute()
        company = self.env.user.company_id
        if company.country_id.code not in ('BE', 'be'):
            return res

        # set company defaults
        module = __name__.split('addons.')[1].split('.')[0]
        transaction = self.env.ref(
            '%s.intrastat_transaction_1' % module)
        if not company.intrastat_transaction_out_invoice:
            company.intrastat_transaction_out_invoice = transaction
        if not company.intrastat_transaction_out_refund:
            company.intrastat_transaction_out_refund = transaction
        if not company.intrastat_transaction_in_invoice:
            company.intrastat_transaction_in_invoice = transaction
        if not company.intrastat_transaction_in_refund:
            company.intrastat_transaction_in_refund = transaction

        # load intrastat_codes
        self.cn_codes = self.env['hs.code'].search([])
        self.cn_lookup = {}
        for i, c in enumerate(self.cn_codes):
            self.cn_lookup[c.local_code] = i
        CN_fqn = 'l10n_be_intrastat_product/data/' \
            + self.CN_file + '_intrastat_codes.csv'
        with tools.file_open(CN_fqn) as CN_file:
            cn_codes = csv.DictReader(CN_file, delimiter=CN_file_delimiter)
            for row in cn_codes:
                self._load_code(row)
        return res
