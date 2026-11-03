# Copyright 2026 - OCA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models

ATC_VERIFACTU_TAX_KEY = "03"


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    verifactu_tax_key = fields.Selection(
        selection="_get_verifactu_tax_keys",
        default=lambda self: self._default_verifactu_tax_key(),
        string="VERI*FACTU tax key",
    )

    @api.model
    def _default_verifactu_tax_key(self):
        agency = self.env.ref(
            "l10n_es_aeat.aeat_tax_agency_canarias", raise_if_not_found=False
        )
        if agency and self.env.company.tax_agency_id == agency:
            return ATC_VERIFACTU_TAX_KEY
        return "01"

    @api.model_create_multi
    def create(self, vals_list):
        agency = self.env.ref(
            "l10n_es_aeat.aeat_tax_agency_canarias", raise_if_not_found=False
        )
        if agency:
            for vals in vals_list:
                if vals.get("verifactu_tax_key"):
                    continue
                company_id = vals.get("company_id") or self.env.company.id
                company = self.env["res.company"].browse(company_id)
                if company.tax_agency_id == agency:
                    vals["verifactu_tax_key"] = ATC_VERIFACTU_TAX_KEY
        return super().create(vals_list)

    @api.model
    def _igic_verifactu_separate_lease_and_recargo(self):
        """El arrendamiento usa igic_re_ex. El recargo IGIC no lleva la clave 18.

        16.0 shipped a dedicated ``igic_lease_ex`` tax and this migration moved
        its pending mappings to ``igic_re_ex``. 17.0 never creates that tax (the
        lease position already maps to ``igic_re_ex``), so the migration is
        re-expressed over ``account.tax`` only; the ``account.tax.template``
        model no longer exists. The recargo correction is still live.
        """
        agency = self.env.ref(
            "l10n_es_aeat.aeat_tax_agency_canarias", raise_if_not_found=False
        )
        key_01 = self.env.ref(
            "l10n_es_verifactu_oca.verifactu_registration_keys_igic_01",
            raise_if_not_found=False,
        )
        key_11 = self.env.ref(
            "l10n_es_verifactu_oca.verifactu_registration_keys_igic_11",
            raise_if_not_found=False,
        )
        ir_model_data = self.env["ir.model.data"].sudo()
        Tax = self.env["account.tax"]
        for company in self.env["res.company"].search([]):
            re_ex_id = company._get_tax_id_from_xmlid("account_tax_template_igic_re_ex")
            re_ex = Tax.browse(re_ex_id) if re_ex_id else Tax
            data_name = f"{company.id}_account_tax_template_igic_lease_ex"
            existing = ir_model_data.search(
                [
                    ("module", "=", "l10n_es_igic"),
                    ("name", "=", data_name),
                    ("model", "=", "account.tax"),
                ],
                limit=1,
            )
            lease_tax = Tax.browse(existing.res_id).exists() if existing else Tax
            lease_fp = self.env.ref(
                f"account.{company.id}_fp_lease_canary", raise_if_not_found=False
            )
            if lease_fp and agency and company.tax_agency_id == agency:
                if lease_fp.verifactu_tax_key != "03":
                    lease_fp.verifactu_tax_key = "03"
                if key_11 and lease_fp.verifactu_registration_key.code not in (
                    "11",
                    "01",
                ):
                    lease_fp.verifactu_registration_key = key_11
            if lease_fp and lease_tax and re_ex:
                lease_lines = lease_fp.tax_ids.filtered(
                    lambda line, tax=lease_tax: line.tax_dest_id == tax
                )
                for line in lease_lines:
                    src = line.tax_src_id
                    duplicate = lease_fp.tax_ids.filtered(
                        lambda candidate, current=line, dest=re_ex, src=src: (
                            candidate.id != current.id
                            and candidate.tax_src_id == src
                            and candidate.tax_dest_id == dest
                        )
                    )
                    if duplicate:
                        line.unlink()
                    else:
                        line.tax_dest_id = re_ex
            referenced = lease_tax and (
                self.env["account.move.line"].search_count(
                    [("tax_ids", "in", lease_tax.ids)]
                )
                or self.env["account.fiscal.position.tax"].search_count(
                    [
                        "|",
                        ("tax_src_id", "=", lease_tax.id),
                        ("tax_dest_id", "=", lease_tax.id),
                    ]
                )
            )
            if lease_tax and not referenced:
                if existing.exists():
                    existing.unlink()
                lease_tax.unlink()
            recargo_fp = self.env.ref(
                f"account.{company.id}_fp_recargo_canary", raise_if_not_found=False
            )
            if (
                key_01
                and recargo_fp
                and recargo_fp.verifactu_tax_key == "03"
                and recargo_fp.verifactu_registration_key.code == "18"
            ):
                recargo_fp.verifactu_registration_key = key_01
        self.env.registry.clear_cache()
