# © 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

import logging

from odoo.tests import common

_logger = logging.getLogger("aeat")


class TestL10nEsAeatModBase(common.SavepointCase):
    accounts = {}
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False
    # These 2 dictionaries below allows to define easily several taxes to apply
    # to invoice lines through the methods _invoice_sale/purchase_create.
    # The structure is:
    # * One dictionary entry per invoice line.
    # * The key of the entry will be the code of the tax.
    # * You can duplicate invoice lines with the same tax using a suffix '//X',
    #   being X any string.
    # * You can include more than one tax in the same invoice line, splitting
    #   each tax code by a comma.
    # * The value of the entry will be a list, being the first element of the
    #   the list, the price_unit amount. The rest of the elements can be for
    #   reference, but not used, like the tax amount in second position.
    taxes_sale = {}
    taxes_purchase = {}
    taxes_result = {}

    @classmethod
    def with_context(cls, *args, **kwargs):
        context = dict(args[0] if args else cls.env.context, **kwargs)
        cls.env = cls.env(context=context)
        return cls

    @classmethod
    def _chart_of_accounts_create(cls):
        _logger.debug("Creating chart of account")
        cls.company = cls.env["res.company"].create(
            {"name": "Spanish test company", "currency_id": cls.env.ref("base.EUR").id}
        )
        cls.chart = cls.env.ref("l10n_es.account_chart_template_pymes")
        cls.env.ref("base.group_multi_company").write({"users": [(4, cls.env.uid)]})
        cls.env.user.write(
            {"company_ids": [(4, cls.company.id)], "company_id": cls.company.id}
        )
        chart = cls.env.ref("l10n_es.account_chart_template_pymes")
        chart.try_loading()
        cls.with_context(company_id=cls.company.id)
        return True

    @classmethod
    def _accounts_search(cls):
        _logger.debug("Searching accounts")
        codes = {
            "472000",
            "473000",
            "477000",
            "475100",
            "475000",
            "600000",
            "700000",
            "430000",
            "410000",
        }
        for code in codes:
            cls.accounts[code] = cls.env["account.account"].search(
                [("company_id", "=", cls.company.id), ("code", "=", code)]
            )
        return True

    @classmethod
    def _print_move_lines(cls, lines):
        _logger.debug(
            "%8s %9s %9s %14s %s", "ACCOUNT", "DEBIT", "CREDIT", "TAX", "TAXES"
        )
        for line in lines:
            _logger.debug(
                "%8s %9s %9s %14s %s",
                line.account_id.code,
                line.debit,
                line.credit,
                line.tax_line_id.description,
                line.tax_ids.mapped("name"),
            )

    @classmethod
    def _print_tax_lines(cls, lines):
        for line in lines:
            _logger.debug(
                "=== [%s] ============================= [%s]",
                line.field_number,
                line.amount,
            )
            cls._print_move_lines(line.move_line_ids)

    @classmethod
    def _get_taxes(cls, descs):
        taxes = cls.env["account.tax"]
        for desc in descs.split(","):
            parts = desc.split(".")
            module = parts[0] if len(parts) > 1 else "l10n_es"
            xml_id = parts[1] if len(parts) > 1 else parts[0]
            if xml_id.lower() != xml_id and len(parts) == 1:
                # shortcut for not changing existing tests with old codes
                xml_id = "account_tax_template_" + xml_id.lower()
            tax_template = cls.env.ref(
                "{}.{}".format(module, xml_id), raise_if_not_found=False
            )
            if tax_template:
                tax = cls.company.get_taxes_from_templates(tax_template)
                taxes |= tax
            if not tax_template or not tax:
                _logger.error("Tax not found: {}".format(desc))
        return taxes

    @classmethod
    def _invoice_sale_create(cls, dt, extra_vals=None):
        data = {
            "company_id": cls.company.id,
            "partner_id": cls.customer.id,
            "invoice_date": dt,
            "move_type": "out_invoice",
            "journal_id": cls.journal_sale.id,
            "invoice_line_ids": [],
        }
        _logger.debug("Creating sale invoice: date = %s" % dt)
        if cls.debug:
            _logger.debug("{:>14} {:>9}".format("SALE TAX", "PRICE"))
        for desc, values in cls.taxes_sale.items():
            if cls.debug:
                _logger.debug("{:>14} {:>9}".format(desc, values[0]))
            # Allow to duplicate taxes skipping the unique key constraint
            line_data = {
                "name": "Test for tax(es) %s" % desc,
                "account_id": cls.accounts["700000"].id,
                "price_unit": values[0],
                "quantity": 1,
            }
            taxes = cls._get_taxes(desc.split("//")[0])
            if taxes:
                line_data["tax_ids"] = [(4, t.id) for t in taxes]
            data["invoice_line_ids"].append((0, 0, line_data))
        if extra_vals:
            data.update(extra_vals)
        inv = cls.env["account.move"].with_user(cls.billing_user).create(data)
        inv.action_post()
        if cls.debug:
            cls._print_move_lines(inv.line_ids)
        return inv

    @classmethod
    def _invoice_purchase_create(cls, dt, extra_vals=None):
        data = {
            "company_id": cls.company.id,
            "partner_id": cls.supplier.id,
            "invoice_date": dt,
            "move_type": "in_invoice",
            "journal_id": cls.journal_purchase.id,
            "invoice_line_ids": [],
        }
        _logger.debug("Creating purchase invoice: date = %s" % dt)
        if cls.debug:
            _logger.debug("{:>14} {:>9}".format("PURCHASE TAX", "PRICE"))
        for desc, values in cls.taxes_purchase.items():
            if cls.debug:
                _logger.debug("{:>14} {:>9}".format(desc, values[0]))
            # Allow to duplicate taxes skipping the unique key constraint
            line_data = {
                "name": "Test for tax(es) %s" % desc,
                "account_id": cls.accounts["600000"].id,
                "price_unit": values[0],
                "quantity": 1,
            }
            taxes = cls._get_taxes(desc.split("//")[0])
            if taxes:
                line_data["tax_ids"] = [(4, t.id) for t in taxes]
            data["invoice_line_ids"].append((0, 0, line_data))
        if extra_vals:
            data.update(extra_vals)
        inv = cls.env["account.move"].with_user(cls.billing_user).create(data)
        inv.sudo().action_post()  # FIXME: Why do we need to do it as sudo?
        if cls.debug:
            cls._print_move_lines(inv.line_ids)
        return inv

    @classmethod
    def _invoice_refund(cls, invoice, dt):
        _logger.debug("Refund {} invoice: date = {}".format(invoice.move_type, dt))
        default_values_list = [
            {"date": dt, "invoice_date": dt, "invoice_payment_term_id": None}
        ]
        inv = invoice.with_user(cls.billing_user)._reverse_moves(default_values_list)
        inv.action_post()
        if cls.debug:
            cls._print_move_lines(inv.line_ids)
        return inv

    @classmethod
    def _journals_create(cls):
        cls.journal_sale = cls.env["account.journal"].create(
            {
                "company_id": cls.company.id,
                "name": "Test journal for sale",
                "type": "sale",
                "code": "TSALE",
                "default_account_id": cls.accounts["700000"].id,
            }
        )
        cls.journal_purchase = cls.env["account.journal"].create(
            {
                "company_id": cls.company.id,
                "name": "Test journal for purchase",
                "type": "purchase",
                "code": "TPUR",
                "default_account_id": cls.accounts["600000"].id,
            }
        )
        cls.journal_misc = cls.env["account.journal"].create(
            {
                "company_id": cls.company.id,
                "name": "Test journal for miscellanea",
                "type": "general",
                "code": "TMISC",
            }
        )
        cls.journal_cash = cls.env["account.journal"].create(
            {
                "company_id": cls.company.id,
                "name": "Test journal for cash",
                "type": "cash",
                "code": "TCSH",
            }
        )
        return True

    @classmethod
    def _partners_create(cls):
        cls.customer = cls.env["res.partner"].create(
            {
                "company_id": cls.company.id,
                "name": "Test customer",
                "property_account_payable_id": cls.accounts["410000"].id,
                "property_account_receivable_id": cls.accounts["430000"].id,
            }
        )
        cls.supplier = cls.env["res.partner"].create(
            {
                "company_id": cls.company.id,
                "name": "Test supplier",
                "property_account_payable_id": cls.accounts["410000"].id,
                "property_account_receivable_id": cls.accounts["430000"].id,
            }
        )
        cls.customer_bank = cls.env["res.partner.bank"].create(
            {
                "partner_id": cls.customer.id,
                "acc_number": "ES66 2100 0418 4012 3456 7891",
            }
        )
        return True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create chart
        cls._chart_of_accounts_create()
        # Create accounts
        cls._accounts_search()
        # Create journals
        cls._journals_create()
        # Create partners
        cls._partners_create()
        # Ensure tax rate environment
        cls.usd = cls.env.ref("base.USD")
        cls.usd.rate_ids.unlink()
        cls.usd.rate_ids = [(0, 0, {"name": "2000-01-01", "rate": "1.2"})]
        # Security groups
        invocing_grp = cls.env.ref("account.group_account_invoice")
        account_user_grp = cls.env.ref("account.group_account_user")
        account_manager_grp = cls.env.ref("account.group_account_manager")
        aeat_grp = cls.env.ref("l10n_es_aeat.group_account_aeat")
        # Create test user
        Users = cls.env["res.users"].with_context(
            {"no_reset_password": True, "mail_create_nosubscribe": True}
        )
        cls.billing_user = Users.create(
            {
                "name": "Billing user",
                "login": "billing_user",
                "email": "billing.user@example.com",
                "groups_id": [(6, 0, [invocing_grp.id])],
            }
        )
        cls.account_user = Users.create(
            {
                "name": "Account user",
                "login": "account_user",
                "email": "account.user@example.com",
                "groups_id": [(6, 0, [account_user_grp.id])],
            }
        )
        cls.account_manager = Users.create(
            {
                "name": "Account manager",
                "login": "account_manager",
                "email": "account.manager@example.com",
                "groups_id": [(6, 0, [account_manager_grp.id, aeat_grp.id])],
            }
        )
