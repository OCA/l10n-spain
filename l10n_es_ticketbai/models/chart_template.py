# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# Copyright 2021 Digital5, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, fields, models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position.template"

    tbai_vat_regime_key = fields.Many2one(
        comodel_name="tbai.vat.regime.key", string="VAT Regime Key", copy=False
    )
    tbai_vat_regime_key2 = fields.Many2one(
        comodel_name="tbai.vat.regime.key", string="VAT Regime 2nd Key", copy=False
    )
    tbai_vat_regime_key3 = fields.Many2one(
        comodel_name="tbai.vat.regime.key", string="VAT Regime 3rd Key", copy=False
    )
    tbai_vat_exemption_ids = fields.One2many(
        comodel_name="account.fp.tbai.tax_template", inverse_name="position_id"
    )


class AccountFiscalPositionTicketBAITaxTemplate(models.Model):
    _name = "account.fp.tbai.tax_template"
    _description = "TicketBAI - Fiscal Position Template Tax Exemptions"
    _rec_name = "tbai_vat_exemption_key"

    position_id = fields.Many2one(
        comodel_name="account.fiscal.position.template",
        string="Fiscal Position",
        required=True,
        ondelete="cascade",
    )
    tax_id = fields.Many2one(
        comodel_name="account.tax.template",
        string="Tax",
        required=True,
        ondelete="cascade",
    )
    tbai_vat_exemption_key = fields.Many2one(
        comodel_name="tbai.vat.exemption.key",
        string="VAT Exemption Key",
        required=True,
        ondelete="restrict",
    )

    _sql_constraints = [
        (
            "position_tax_uniq",
            "UNIQUE(position_id,tax_id)",
            _("Tax must be unique per fiscal position!"),
        )
    ]


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    def _get_fp_vals(self, company, position):
        res = super()._get_fp_vals(company, position)
        res.update(
            {
                "tbai_vat_regime_key": position.tbai_vat_regime_key.id,
                "tbai_vat_regime_key2": position.tbai_vat_regime_key2.id,
                "tbai_vat_regime_key3": position.tbai_vat_regime_key3.id,
            }
        )
        return res

    def create_record_with_xmlid(self, company, template, model, vals):
        res_id = super().create_record_with_xmlid(company, template, model, vals)
        if "account.fiscal.position" == model:
            fiscal_position = self.env["account.fiscal.position"].browse(res_id)
            tbai_vat_exemptions = []
            for exemption in template.tbai_vat_exemption_ids:
                tax = company.get_taxes_from_templates(exemption.tax_id)
                if 1 == len(tax):
                    tbai_vat_exemptions.append(
                        (
                            0,
                            0,
                            {
                                "tax_id": tax.id,
                                "tbai_vat_exemption_key": (
                                    exemption.tbai_vat_exemption_key.id
                                ),
                            },
                        )
                    )
            if tbai_vat_exemptions:
                fiscal_position.tbai_vat_exemption_ids = tbai_vat_exemptions
        return res_id
