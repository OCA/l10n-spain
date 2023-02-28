# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import os
from datetime import date

from odoo.tests.common import tagged

from odoo.addons.l10n_es_ticketbai_api.tests.common import TestL10nEsTicketBAIAPI


@tagged("post_install", "-at_install")
class TestL10nEsTicketBAI(TestL10nEsTicketBAIAPI):
    def create_account_billing(self):
        return (
            self.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Accountant",
                    "company_id": self.main_company.id,
                    "login": "accountuser",
                    "email": "accountuser@yourcompany.com",
                    "groups_id": [
                        (
                            6,
                            0,
                            [
                                self.group_user.id,
                                self.res_users_account_billing.id,
                                self.partner_manager.id,
                            ],
                        )
                    ],
                }
            )
        )

    def create_account_manager(self):
        return (
            self.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Adviser",
                    "company_id": self.main_company.id,
                    "login": "accountmanager",
                    "email": "accountmanager@yourcompany.com",
                    "groups_id": [
                        (
                            6,
                            0,
                            [
                                self.group_user.id,
                                self.res_users_account_manager.id,
                                self.partner_manager.id,
                            ],
                        )
                    ],
                }
            )
        )

    def create_draft_invoice(
        self,
        uid,
        fp,
        partner,
        only_service=False,
        company_id=None,
        invoice_type="out_invoice",
        journal_id=None,
        context=None,
    ):
        if not context:
            context = {}
        invoice_line_ids = []

        if not only_service:
            invoice_line_ids.append(
                (
                    0,
                    0,
                    {
                        "product_id": self.product_delivery.id,
                        "quantity": 1,
                        "price_unit": 100.0,
                        "name": "TBAI Invoice Line Test - delivery 1",
                        "account_id": self.account_revenue.id,
                        "tax_ids": [
                            (
                                6,
                                0,
                                fp.map_tax([self.product_delivery.taxes_id]).mapped(
                                    "id"
                                ),
                            )
                        ],
                    },
                )
            )

            invoice_line_ids.append(
                (
                    0,
                    0,
                    {
                        "product_id": self.product_delivery.id,
                        "quantity": 1,
                        "price_unit": 100.0,
                        "name": "TBAI Invoice Line Test - delivery 2",
                        "account_id": self.account_revenue.id,
                        "tax_ids": [
                            (
                                6,
                                0,
                                fp.map_tax([self.product_delivery.taxes_id]).mapped(
                                    "id"
                                ),
                            )
                        ],
                    },
                )
            )

        invoice_line_ids.append(
            (
                0,
                0,
                {
                    "product_id": self.product_service.id,
                    "quantity": 1,
                    "discount": 10.0,
                    "price_unit": 100.0,
                    "name": "TBAI Invoice Line Test - service",
                    "account_id": self.account_revenue.id,
                    "tax_ids": [
                        (
                            6,
                            0,
                            fp.map_tax([self.product_service.taxes_id]).mapped("id"),
                        )
                    ],
                },
            )
        )

        invoice_vals = {
            "partner_id": partner,
            "currency_id": self.env.ref("base.EUR").id,
            "invoice_date": str(date.today()),
            "tbai_date_operation": str(date.today()),
            "fiscal_position_id": fp.id,
            "invoice_line_ids": invoice_line_ids,
            "company_id": company_id or self.main_company.id,
        }

        if journal_id:
            invoice_vals["journal_id"] = journal_id.id

        invoice = (
            self.env["account.move"]
            .with_user(uid)
            .with_context(default_move_type=invoice_type)
            .create(invoice_vals)
        )

        return invoice

    def create_aeat_certificate(self):
        test_dir_path = os.path.abspath(os.path.dirname(__file__))
        p12_filepath = "%s/certs/ciudadano_act.p12" % test_dir_path
        with open(p12_filepath, "rb") as f:
            p12_file = f.read()
        pem_filepath = "%s/certs/private_up_8mgwq.pem" % test_dir_path
        crt_filepath = "%s/certs/public_362gar7l.crt" % test_dir_path
        aeat_certificate = self.env["l10n.es.aeat.certificate"].create(
            {
                "name": "TicketBAI - Test certificate",
                "folder": "TicketBAI",
                "file": p12_file,
                "private_key": pem_filepath,
                "public_key": crt_filepath,
                "company_id": self.main_company.id,
            }
        )
        aeat_certificate.action_active()
        return aeat_certificate

    def create_product(self, product_name, product_type="consu", product_taxes=None):
        def create_template():
            template_model = self.env["product.template"]
            template_dict = {"name": product_name, "type": product_type}
            return template_model.create(template_dict)

        product_obj = create_template().product_variant_ids[0]
        if product_taxes:
            product_obj["taxes_id"] = [(6, 0, product_taxes)]
        return product_obj

    def setUp(self):
        super().setUp()
        aeat_certificate = self.create_aeat_certificate()
        self.main_company.tbai_aeat_certificate_id = aeat_certificate.id
        self.product_delivery = self.env.ref("product.product_delivery_01")
        self.product_service = self.env.ref("product.product_product_6")
        self.group_user = self.env.ref("base.group_user")  # Employee
        self.res_users_account_billing = self.env.ref(
            "account.group_account_invoice"
        )  # Billing
        self.res_users_account_manager = self.env.ref(
            "account.group_account_manager"
        )  # Billing Manager
        self.partner_manager = self.env.ref("base.group_partner_manager")
        self.account_billing = self.create_account_billing()  # Billing user
        self.account_manager = self.create_account_manager()  # Billing Manager user
        self.account_receivable = self.env["account.account"].search(
            [
                (
                    "account_type",
                    "=",
                    "asset_receivable",
                ),
                ("company_id", "=", self.main_company.id),
            ],
            limit=1,
        )
        self.account_revenue = self.env["account.account"].search(
            [
                (
                    "account_type",
                    "=",
                    "income",
                ),
                ("company_id", "=", self.main_company.id),
            ],
            limit=1,
        )
        # Exenciones en operaciones interiores
        self.vat_exemption_E1 = self.env.ref("l10n_es_ticketbai.tbai_vat_exemption_E1")
        # Exportaciones de mercancías
        self.vat_exemption_E2 = self.env.ref("l10n_es_ticketbai.tbai_vat_exemption_E2")
        # Entregas a otro estado miembro
        self.vat_exemption_E5 = self.env.ref("l10n_es_ticketbai.tbai_vat_exemption_E5")
        # Otros
        self.vat_exemption_E6 = self.env.ref("l10n_es_ticketbai.tbai_vat_exemption_E6")
        # Bienes
        self.tax_21b = self.env.ref("l10n_es.1_account_tax_template_s_iva21b")
        # Servicios
        self.tax_10s = self.env.ref("l10n_es.1_account_tax_template_s_iva10s")
        # Retenciones a cuenta IRPF 15%
        self.tax_irpf_15 = self.env.ref("l10n_es.1_account_tax_template_s_irpf15")
        # 1.4% Recargo Equivalencia Ventas
        self.tax_req14 = self.env.ref("l10n_es.1_account_tax_template_s_req014")
        # 5.2% Recargo Equivalencia Ventas
        self.tax_req52 = self.env.ref("l10n_es.1_account_tax_template_s_req52")
        # Bienes intracomunitarios
        self.tax_iva0_ic = self.env.ref("l10n_es.1_account_tax_template_s_iva0_ic")
        # Servicios intracomunitarios
        self.tax_iva0_sp_i = self.env.ref("l10n_es.1_account_tax_template_s_iva0_sp_i")
        # Bienes extracomunitarios
        self.tax_iva0_e = self.env.ref("l10n_es.1_account_tax_template_s_iva0_e")
        # Servicios extracomunitarios
        self.tax_iva0_sp_e = self.env.ref("l10n_es.1_account_tax_template_s_iva_e")
        # IVA Exento Repercutido Sujeto
        self.tax_iva0_exento_sujeto = self.env.ref(
            "l10n_es.1_account_tax_template_s_iva0"
        )
        self.product_delivery.taxes_id = [(6, 0, [self.tax_21b.id])]
        self.product_service.taxes_id = [(6, 0, [self.tax_10s.id])]
        # 07 - Régimen especial criterio de caja
        # 05 - Régimen especial de agencias de viajes
        # 01 - Régimen general
        self.fiscal_position_national = self.env["account.fiscal.position"].create(
            {
                "name": "TBAI Fiscal Position - Régimen Nacional",
                "tbai_vat_regime_key": self.env.ref(
                    "l10n_es_ticketbai.tbai_vat_regime_07"
                ).id,
                "tbai_vat_regime_key2": self.env.ref(
                    "l10n_es_ticketbai.tbai_vat_regime_05"
                ).id,
                "tbai_vat_regime_key3": self.env.ref(
                    "l10n_es_ticketbai.tbai_vat_regime_01"
                ).id,
                "tbai_vat_exemption_ids": [
                    (
                        0,
                        0,
                        {
                            "tax_id": self.tax_iva0_exento_sujeto.id,
                            "tbai_vat_exemption_key": self.vat_exemption_E1.id,
                        },
                    )
                ],
            }
        )
        self.fiscal_position_surcharge = self.env["account.fiscal.position"].create(
            {
                "name": "TBAI Fiscal Position - Surcharge",
                "tbai_vat_regime_key": self.env.ref(
                    "l10n_es_ticketbai.tbai_vat_regime_01"
                ).id,
                "tax_ids": [
                    (
                        0,
                        0,
                        {"tax_src_id": self.tax_10s.id, "tax_dest_id": self.tax_10s.id},
                    ),
                    (
                        0,
                        0,
                        {
                            "tax_src_id": self.tax_10s.id,
                            "tax_dest_id": self.tax_req14.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {"tax_src_id": self.tax_21b.id, "tax_dest_id": self.tax_21b.id},
                    ),
                    (
                        0,
                        0,
                        {
                            "tax_src_id": self.tax_21b.id,
                            "tax_dest_id": self.tax_req52.id,
                        },
                    ),
                ],
            }
        )
        self.fiscal_position_irpf15 = self.env["account.fiscal.position"].create(
            {
                "name": "TBAI Fiscal Position - Withholding Tax 15%",
                "tbai_vat_regime_key": self.env.ref(
                    "l10n_es_ticketbai.tbai_vat_regime_01"
                ).id,
                "tax_ids": [
                    (
                        0,
                        0,
                        {"tax_src_id": self.tax_21b.id, "tax_dest_id": self.tax_21b.id},
                    ),
                    (
                        0,
                        0,
                        {
                            "tax_src_id": self.tax_21b.id,
                            "tax_dest_id": self.tax_irpf_15.id,
                        },
                    ),
                ],
            }
        )
        self.fiscal_position_ic = self.env["account.fiscal.position"].create(
            {
                "name": "TBAI Fiscal Position - European Union "
                "(Intracommunity Operations)",
                "tbai_vat_regime_key": self.env.ref(
                    "l10n_es_ticketbai.tbai_vat_regime_01"
                ).id,
                "tbai_vat_exemption_ids": [
                    (
                        0,
                        0,
                        {
                            "tax_id": self.tax_iva0_ic.id,
                            "tbai_vat_exemption_key": self.vat_exemption_E5.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "tax_id": self.tax_iva0_sp_i.id,
                            "tbai_vat_exemption_key": self.vat_exemption_E5.id,
                        },
                    ),
                ],
                "tax_ids": [
                    (
                        0,
                        0,
                        {
                            "tax_src_id": self.tax_21b.id,
                            "tax_dest_id": self.tax_iva0_ic.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "tax_src_id": self.tax_10s.id,
                            "tax_dest_id": self.tax_iva0_sp_i.id,
                        },
                    ),
                ],
            }
        )
        self.fiscal_position_e = self.env["account.fiscal.position"].create(
            {
                "name": "TBAI Fiscal Position - Exports (Extracommunity Operations)",
                "tbai_vat_regime_key": self.env.ref(
                    "l10n_es_ticketbai.tbai_vat_regime_02"
                ).id,
                "tbai_vat_exemption_ids": [
                    (
                        0,
                        0,
                        {
                            "tax_id": self.tax_iva0_e.id,
                            "tbai_vat_exemption_key": self.vat_exemption_E2.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "tax_id": self.tax_iva0_sp_e.id,
                            "tbai_vat_exemption_key": self.vat_exemption_E6.id,
                        },
                    ),
                ],
                "tax_ids": [
                    (
                        0,
                        0,
                        {
                            "tax_src_id": self.tax_21b.id,
                            "tax_dest_id": self.tax_iva0_e.id,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "tax_src_id": self.tax_10s.id,
                            "tax_dest_id": self.tax_iva0_sp_e.id,
                        },
                    ),
                ],
            }
        )
        self.fiscal_position_ipsi_igic = self.main_company.get_fps_from_templates(
            self.env.ref("l10n_es.fp_not_subject_tai")
        )
        self.tbai_journal = self.env["account.journal"].create(
            {
                "name": "Tbai journal",
                "type": "sale",
                "code": "TBAI",
            }
        )
        self.non_tbai_journal = self.env["account.journal"].create(
            {
                "name": "Non-Tbai journal",
                "type": "sale",
                "code": "NTBAI",
                "tbai_send_invoice": False,
            }
        )
