# Copyright 2026 Studio73 - Pablo Cortés <pablo.cortes@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command, fields, models

from odoo.addons.account_banking_sepa_direct_debit.tests.common import (
    AccountBankingSepaDirectDebitCommon,
)


class AccountBankingSepaDirectDebitFSDDCommon(AccountBankingSepaDirectDebitCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.other_company = cls.env["res.company"].create(
            {
                "name": "Another FSDD Test Company",
                "currency_id": cls.eur_currency.id,
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.other_company.partner_id.company_id = cls.other_company
        cls._test_user.company_ids = [Command.link(cls.other_company.id)]
        other_company_account = cls.env["account.account"].create(
            {
                "code": "NC2222",
                "name": "FSDD Test Company Expense Account",
                "account_type": "expense",
                "company_ids": [Command.set(cls.other_company.ids)],
            }
        )
        other_company_bank = cls._create_partner_bank(
            cls.env,
            cls.other_company.partner_id,
            "ES5220820012345678901234",
            cls.other_company,
        )
        cls.other_company_journal = cls.env["account.journal"].create(
            {
                "name": "Another Company Bank Journal",
                "type": "bank",
                "code": "BNKTC",
                "company_id": cls.other_company.id,
                "bank_account_id": other_company_bank.id,
                "inbound_payment_method_line_ids": [
                    Command.create(
                        {
                            "payment_method_id": cls.payment_mode.payment_method_id.id,
                            "payment_account_id": other_company_account.id,
                        }
                    )
                ],
            }
        )
        cls.other_company_payment_mode = cls.env["account.payment.mode"].create(
            {
                "name": "SEPA Direct Debit of customers in another company",
                "company_id": cls.other_company.id,
                "payment_method_id": cls.payment_mode.payment_method_id.id,
                "bank_account_link": "fixed",
                "fixed_journal_id": cls.other_company_journal.id,
                "sepa_creditor_identifier": False,
            }
        )

    def create_invoice(
        self, partner_id, mandate, price_unit, payment_mode=None, inv_type="out_invoice"
    ) -> models.Model:
        invoice_lines = [
            Command.create(
                {
                    "name": "Great service",
                    "quantity": 1,
                    "account_id": self.account_revenue_company_B.id,
                    "price_unit": price_unit,
                }
            )
        ]
        invoice = self.invoice_model.create(
            {
                "partner_id": partner_id,
                "reference_type": "none",
                "currency_id": self.eur_currency.id,
                "move_type": inv_type,
                "journal_id": self.journal_sale_company_B.id,
                "date": fields.Date.today(),
                "payment_mode_id": (payment_mode or self.payment_mode).id,
                "mandate_id": mandate.id if mandate else False,
                "invoice_line_ids": invoice_lines,
            }
        )
        invoice.action_post()
        return invoice
