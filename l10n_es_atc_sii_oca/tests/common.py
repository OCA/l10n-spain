# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from datetime import date

from odoo.tests import tagged

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

ATC_AGENCY_XMLID = "l10n_es_aeat.aeat_tax_agency_canarias"

# IGIC repercutido (clave 01 / SFESB): sufijo plantilla → TipoImpositivo esperado
IGIC_SALE_RATES = (
    ("igic_r_0", "0"),
    ("igic_r_3", "3"),
    ("igic_r_5", "5"),
    ("igic_r_7", "7"),
    ("igic_r_9_5", "9.5"),
    ("igic_r_15", "15"),
    ("igic_r_20", "20"),
)


@tagged("post_install", "-at_install", "atc_sii_payload")
class TestL10nEsAtcSiiPayloadBase(TestL10nEsAeatModBase):
    """Empresa IGIC canaria con agencia ATC para aserciones de payload SII."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.maxDiff = None
        cls._skip_if_no_canary_igic()
        cls._configure_atc_company()
        cls._configure_partners()
        cls.product = cls.env["product.product"].create(
            {
                "name": "ATC SII test product",
                "sale_ok": True,
                "purchase_ok": True,
            }
        )
        cls.journal_sale.sii_enabled = True
        cls.journal_purchase.sii_enabled = True
        cls._fp_national = cls._get_fiscal_position("canary_1")
        cls._fp_export = cls._get_fiscal_position("extra_canary")
        cls._fp_export.write({"sii_partner_identification_type": "3"})
        cls._fp_isp = cls._get_fiscal_position("ispn_canary")
        cls._fp_retailer = cls._get_fiscal_position("retailer_canary")
        for fp in (cls._fp_national, cls._fp_export, cls._fp_isp, cls._fp_retailer):
            if hasattr(fp, "aeat_active") and not fp.aeat_active:
                fp.aeat_active = True
            if hasattr(fp, "sii_registration_key_sale"):
                fp.sii_registration_key_sale = False
            if hasattr(fp, "sii_registration_key_purchase"):
                fp.sii_registration_key_purchase = False

    @classmethod
    def _chart_of_accounts_create(cls):
        cls.company = cls.env["res.company"].create(
            {
                "name": "Canary ATC SII test company",
                "currency_id": cls.env.ref("base.EUR").id,
            }
        )
        cls.env["account.chart.template"].try_loading(
            "es_canary_pymes", company=cls.company, install_demo=False
        )
        cls.env.ref("base.group_multi_company").write({"users": [(4, cls.env.uid)]})
        cls.env.user.write(
            {"company_ids": [(4, cls.company.id)], "company_id": cls.company.id}
        )
        cls.with_context(company_id=cls.company.id)
        return True

    @classmethod
    def _skip_if_no_canary_igic(cls):
        tax_id = cls.company._get_tax_id_from_xmlid("account_tax_template_igic_r_7")
        if not tax_id:
            raise cls.skipTest(
                "Canary IGIC chart (l10n_es_igic / es_canary_pymes) is required "
                "for ATC SII payload tests."
            )

    @classmethod
    def _configure_atc_company(cls):
        atc_agency = cls.env.ref(ATC_AGENCY_XMLID)
        cls.company.write(
            {
                "sii_enabled": True,
                "sii_test": True,
                "sii_description_method": "manual",
                "tax_agency_id": atc_agency.id,
            }
        )
        if not cls.company.vat:
            cls.company.partner_id.write({"vat": "ESA12345674"})

    @classmethod
    def _configure_partners(cls):
        cls.customer.write(
            {
                "name": "ATC SII customer",
                "vat": "A12345674",
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.supplier.write(
            {
                "name": "ATC SII supplier",
                "vat": "B12345674",
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.partner_export = cls.env["res.partner"].create(
            {"name": "ATC export customer", "country_id": cls.env.ref("base.us").id}
        )
        cls.partner_simplified = cls.env["res.partner"].create(
            {
                "name": "ATC simplified customer",
                "aeat_simplified_invoice": True,
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.partner_aapp = (
            cls.env["res.partner"]
            .with_context(no_vat_validation=True)
            .create(
                {
                    "name": "ATC AAPP obra",
                    "vat": "P2813800H",
                    "country_id": cls.env.ref("base.es").id,
                }
            )
        )

    @classmethod
    def _get_fiscal_position(cls, suffix):
        candidates = (
            f"account.{cls.company.id}_fp_{suffix}",
            f"l10n_es.fp_{suffix}",
            f"l10n_es_igic.fp_{suffix}",
        )
        for xmlid in candidates:
            fp = cls.env.ref(xmlid, raise_if_not_found=False)
            if fp:
                return fp
        fps = cls.env["account.fiscal.position"].search(
            [
                ("company_id", "=", cls.company.id),
                ("name", "ilike", suffix.replace("_", " ")),
            ],
            limit=1,
        )
        if fps:
            return fps
        raise ValueError(f"Fiscal position not found for suffix {suffix!r}")

    def _tax(self, template_suffix):
        tax_id = self.company._get_tax_id_from_xmlid(
            f"account_tax_template_{template_suffix}"
        )
        self.assertTrue(tax_id, f"Tax template {template_suffix} not in Canary chart")
        return self.env["account.tax"].browse(tax_id)

    def _reg_key(self, code, move_type="out_invoice"):
        key_type = "sale" if move_type.startswith("out") else "purchase"
        key = self.env["aeat.sii.mapping.registration.keys"].search(
            [("code", "=", code), ("type", "=", key_type)],
            limit=1,
        )
        self.assertTrue(key, f"SII registration key {code} ({key_type}) missing")
        return key

    def _create_atc_invoice(
        self,
        *,
        move_type="out_invoice",
        partner=None,
        fiscal_position=None,
        taxes=None,
        price_unit=100.0,
        reg_key_code="01",
        invoice_date=None,
        extra_vals=None,
        post=True,
    ):
        is_sale = move_type.startswith("out")
        partner = partner or (self.customer if is_sale else self.supplier)
        fiscal_position = fiscal_position or self._fp_national
        taxes = taxes or self._tax("igic_r_7")
        invoice_date = invoice_date or date(2026, 3, 15)
        vals = {
            "company_id": self.company.id,
            "partner_id": partner.id,
            "fiscal_position_id": fiscal_position.id,
            "journal_id": self.journal_sale.id if is_sale else self.journal_purchase.id,
            "invoice_date": invoice_date,
            "move_type": move_type,
            "sii_registration_key": self._reg_key(reg_key_code, move_type).id,
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "name": "ATC SII test line",
                        "product_id": self.product.id,
                        "account_id": (
                            self.accounts["700000"].id
                            if is_sale
                            else self.accounts["600000"].id
                        ),
                        "price_unit": price_unit,
                        "quantity": 1,
                        "tax_ids": [(6, 0, taxes.ids)],
                    },
                )
            ],
        }
        if extra_vals:
            vals.update(extra_vals)
        move = self.env["account.move"].create(vals)
        if post:
            move.action_post()
        return move

    def _payload(self, move):
        return move._get_aeat_invoice_dict()

    def _payload_json(self, move):
        return json.dumps(self._payload(move))

    def _assert_no_iva_keys(self, payload):
        dump = json.dumps(payload)
        self.assertNotIn("DesgloseIVA", dump)
        self.assertNotIn("DetalleIVA", dump)

    def _walk_payload(self, node, key):
        found = []

        def walk(item):
            if isinstance(item, dict):
                if key in item:
                    value = item[key]
                    if isinstance(value, list):
                        found.extend(value)
                    elif isinstance(value, dict):
                        found.append(value)
                for value in item.values():
                    walk(value)
            elif isinstance(item, list):
                for sub in item:
                    walk(sub)

        walk(node)
        return found

    def _detalle_igic(self, payload):
        return self._walk_payload(payload, "DetalleIGIC")

    def _factura_expedida(self, payload):
        if "SuministroLRFacturasEmitidas" in payload:
            return payload["SuministroLRFacturasEmitidas"][
                "RegistroLRFacturasEmitidas"
            ]["FacturaExpedida"]
        return payload["FacturaExpedida"]

    def _factura_recibida(self, payload):
        if "SuministroLRFacturasRecibidas" in payload:
            return payload["SuministroLRFacturasRecibidas"][
                "RegistroLRFacturasRecibidas"
            ]["FacturaRecibida"]
        return payload["FacturaRecibida"]

    def _periodo_liquidacion(self, payload):
        if "SuministroLRFacturasEmitidas" in payload:
            return payload["SuministroLRFacturasEmitidas"][
                "RegistroLRFacturasEmitidas"
            ]["PeriodoLiquidacion"]
        if "SuministroLRFacturasRecibidas" in payload:
            return payload["SuministroLRFacturasRecibidas"][
                "RegistroLRFacturasRecibidas"
            ]["PeriodoLiquidacion"]
        return payload["PeriodoLiquidacion"]

    def _get_or_create_fp(self, name, **extra):
        fp = self.env["account.fiscal.position"].search(
            [("company_id", "=", self.company.id), ("name", "=", name)],
            limit=1,
        )
        if not fp:
            fp = self.env["account.fiscal.position"].create(
                {"name": name, "company_id": self.company.id, **extra}
            )
        else:
            fp.write(extra)
        return fp
