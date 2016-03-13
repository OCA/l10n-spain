# -*- coding: utf-8 -*-
# © 2016 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp.tests import common
from openerp import tools
from lxml import etree
import base64
import logging


def log(message):
    logging.getLogger().error(message)


def _text_compare(t1, t2):
    if t1 == '*' or t2 == '*' or (not t1 and not t2):
        return True
    return (t1 or '').strip() == (t2 or '').strip()


def _xml_compare(tree1, tree2, reporter=None):
    """lxml tree comparer based on Ian Bicking's formencode implementation."""
    if not reporter:
        reporter = log
    if tree1.tag != tree2.tag:
        reporter('Tags do not match: %s and %s' % (tree1.tag, tree2.tag))
        return False
    for name, value in tree1.attrib.items():
        if tree2.attrib.get(name) != value:
            reporter('Attributes do not match: %s=%r, %s=%r'
                     % (name, value, name, tree2.attrib.get(name)))
            return False
    for name in tree2.attrib.keys():
        if name not in tree1.attrib:
            reporter('tree2 has an attribute tree1 is missing: %s' % name)
            return False
    if not _text_compare(tree1.text, tree2.text):
        reporter('text: %r != %r' % (tree1.text, tree2.text))
        return False
    if not _text_compare(tree1.tail, tree2.tail):
        reporter('tail: %r != %r' % (tree1.tail, tree2.tail))
        return False
    cl1 = tree1.getchildren()
    cl2 = tree2.getchildren()
    if len(cl1) != len(cl2):
        reporter('children length differs for %s, %i != %i' % (
            tree1.tag, len(cl1), len(cl2)))
        return False
    i = 0
    for c1, c2 in zip(cl1, cl2):
        i += 1
        if not _xml_compare(c1, c2, reporter=reporter):
            return False
    return True


class TestL10nEsFacturae(common.TransactionCase):
    def setUp(self):
        super(TestL10nEsFacturae, self).setUp()
        self.tax_code = self.env['account.tax.code'].create({
            'name': 'Test tax code',
        })
        self.tax = self.env['account.tax'].create({
            'name': 'Test tax',
            'type': 'percent',
            'amount': 0.21,
            'type_tax_use': 'sale',
            'tax_code_id': self.tax_code.id,
        })
        self.state = self.env['res.country.state'].create({
            'name': 'Ciudad Real',
            'code': '13',
            'country_id': self.ref('base.es'),
        })
        self.partner = self.env['res.partner'].create({
            'name': 'Cliente de prueba',
            'street': 'C/ Ejemplo, 13',
            'zip': '13700',
            'city': 'Tomelloso',
            'state_id': self.state.id,
            'country_id': self.ref('base.es'),
            'vat': 'ES05680675C',
        })
        self.journal = self.env['account.journal'].create({
            'name': 'Test journal',
            'code': 'TEST',
            'type': 'sale',
            'currency': self.ref('base.USD'),
        })
        self.invoice = self.env['account.invoice'].create({
            'partner_id': self.partner.id,
            'account_id': self.partner.property_account_receivable.id,
            'journal_id': self.journal.id,
            'date_invoice': '2016-03-12',
            'invoice_line': [
                (0, 0, {
                    'name': 'Producto de prueba',
                    'quantity': 1.0,
                    'price_unit': 100.0,
                    'invoice_line_tax_id': [(6, 0, self.tax.ids)],
                })],
        })

    def test_facturae_generation(self):
        self.invoice.signal_workflow('invoice_open')
        self.invoice.number = '2999/99999'
        wizard = self.env['create.facturae'].create({})
        wizard.with_context(active_ids=self.invoice.ids).create_facturae_file()
        test_facturae = etree.parse(tools.file_open(
            "facturae_test.xml", subdir="addons/l10n_es_facturae/tests"))
        generated_facturae = etree.fromstring(
            base64.b64decode(wizard.facturae))
        self.assertTrue(_xml_compare(
            test_facturae.getroot(), generated_facturae, log))
