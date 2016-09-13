# -*- coding: utf-8 -*-
# Copyright 2010 Pexego Sistemas Informaticos
# Copyright 2012 Pedro Manuel Baeza <pedro.baeza@tecnativa.com>
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import operator
from openerp import fields, models, _

SPANISH_CHARTS = [
    'l10n_es.account_chart_template_common',
    'l10n_es.account_chart_template_assoc',
    'l10n_es.account_chart_template_pymes',
    'l10n_es.account_chart_template_full',
]

_LP_ACCOUNT_MAPPING = [
    ('6%', '129%', u"Compras y gastos"),
    ('7%', '129%', u"Ventas e ingresos"),
]

_NLP_ACCOUNT_MAPPING = [
    ('800%', '133%', False),
    ('802%', '133%', False),
    ('810%', '1340%0', False),
    ('811%', '1341%0', False),
    ('812%', '1340%0', False),
    ('813%', '1341%0', False),
    ('820%', '135%0', False),
    ('821%', '135%0', False),
    ('830%', '13', False),  # Can be any 13? account, like 130 or 133
    ('833%', '13', False),  # Can be any 13? account, like 130 or 133
    ('834%', '137%0', False),
    ('835%', '137%0', False),
    ('835%', '137%0', False),
    ('838%', '133%0', False),
    ('840%', '130%0', False),
    ('841%', '131%0', False),
    ('842%', '132%0', False),
    ('850%', '115%0', False),
    ('851%', '115%0', False),
    ('860%', '136%0', False),
    ('862%', '136%0', False),
    ('890%', '133%0', False),
    ('892%', '133%0', False),
    ('900%', '133%', False),
    ('902%', '133%', False),
    ('910%', '1340%0', False),
    ('911%', '1341%0', False),
    ('912%', '1340%0', False),
    ('913%', '1341%0', False),
    ('920%', '135%0', False),
    ('921%', '135%0', False),
    ('940%', '130%0', False),
    ('941%', '131%0', False),
    ('942%', '132%0', False),
    ('950%', '115%0', False),
    ('951%', '115%0', False),
    ('960%', '136%0', False),
    ('962%', '136%0', False),
    ('990%', '133%0', False),
    ('991%', '133%0', False),
    ('992%', '133%0', False),
    ('993%', '133%0', False),
]

_C_ACCOUNT_MAPPING = [
    ('1%', False, u"Financiación básica"),
    ('2%', False, u"Activo no corriente"),
    ('3%', False, u"Existencias"),
    ('4%', False, u"Acreedores y deudores"),
    ('5%', False, u"Cuentas financieras"),
]

_CLOSING_TYPE_DEFAULT = 'balance'
_CLOSING_TYPES = {
    'account.data_account_type_receivable': 'unreconciled',
    'account.data_account_type_payable': 'unreconciled',
    # 'l10n_es.account_type_tax': 'unreconciled',
}


class AccountFiscalyearClosing(models.Model):
    _inherit = 'account.fiscalyear.closing'

    def _lp_account_mapping_get(self, company):
        account_mappings = self._account_mappings_get(
            company, _LP_ACCOUNT_MAPPING)
        return {
            'name': _("Loss & Profit"),
            'sequence': 10,
            'code': 'LP',
            'move_type': 'closing',
            'enable': True,
            'journal_id': self._default_journal().id,
            'mapping_ids': [(0, 0, m) for m in account_mappings],
            'closing_type_default': _CLOSING_TYPE_DEFAULT,
        }

    def _nlp_account_mapping_get(self, company):
        account_mappings = self._account_mappings_get(
            company, _NLP_ACCOUNT_MAPPING)
        return {
            'name': _("Net Loss & Profit"),
            'sequence': 11,
            'code': 'NLP',
            'move_type': 'closing',
            'enable': False,
            'journal_id': self._default_journal().id,
            'mapping_ids': [(0, 0, m) for m in account_mappings],
            'closing_type_default': _CLOSING_TYPE_DEFAULT,
        }

    def _c_account_mapping_get(self, company):
        account_mappings = self._account_mappings_get(
            company, _C_ACCOUNT_MAPPING)
        account_closing_types = self._account_closing_types_get(_CLOSING_TYPES)
        data = {
            'name': _("Fiscal Year Closing"),
            'sequence': 50,
            'code': 'C',
            'move_type': 'closing',
            'enable': True,
            'journal_id': self._default_journal().id,
            'mapping_ids': [(0, 0, m) for m in account_mappings],
            'closing_type_default': _CLOSING_TYPE_DEFAULT,
            'closing_type_ids': [(0, 0, m) for m in account_closing_types]
        }
        return data

    def _o_account_mapping_get(self, company):
        return {
            'name': _("Fiscal Year Opening"),
            'sequence': 90,
            'code': 'O',
            'inverse': 'C',
            'reconcile': True,
            'move_type': 'opening',
            'enable': True,
            'journal_id': self._default_journal().id,
            'closing_type_default': _CLOSING_TYPE_DEFAULT,
        }

    def _default_move_config_ids(self):
        configs = super(AccountFiscalyearClosing, self).\
            _default_move_config_ids()
        spanish_charts = reduce(
            operator.add, [self.env.ref(x) for x in SPANISH_CHARTS])
        spanish_full_chart = self.env.ref(
            'l10n_es.account_chart_template_full')
        company = self._default_company()
        # Add configurations only if company chart template is Spanish
        if company.chart_template_id in spanish_charts:
            configs.append((0, 0, self._lp_account_mapping_get(company)))
            # Net L&P move required only in Spanish full template
            if company.chart_template_id == spanish_full_chart:
                configs.append((0, 0, self._nlp_account_mapping_get(company)))
            configs.append((0, 0, self._c_account_mapping_get(company)))
            configs.append((0, 0, self._o_account_mapping_get(company)))
        return configs

    move_config_ids = fields.One2many(default=_default_move_config_ids)
