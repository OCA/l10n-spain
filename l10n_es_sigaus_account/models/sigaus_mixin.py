# Copyright 2023 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import SUPERUSER_ID, fields, models


class SigausMixin(models.AbstractModel):
    _name = "sigaus.mixin"
    _description = "Sigaus Mixin"

    is_sigaus = fields.Boolean(
        compute="_compute_is_sigaus",
        string="Subject to SIGAUS",
        store=True,
        readonly=False,
    )
    sigaus_is_date = fields.Boolean(
        compute="_compute_sigaus_is_date",
        store=True,
        help="Technical field to determine whether the date of a document subject to "
        "SIGAUS is equal or after the date selected in the company from which SIGAUS "
        "has to be applied.",
    )
    sigaus_has_line = fields.Boolean(compute="_compute_sigaus_has_line")
    # It cannot be a related field as sigaus.mixin does not have a company_id field
    sigaus_company = fields.Boolean(compute="_compute_sigaus_company")
    sigaus_automated_exception_id = fields.Many2one(
        comodel_name="mail.activity", readonly=True
    )

    _sigaus_secondary_unit_fields = {}

    def _compute_is_sigaus(self):
        for rec in self:
            rec.is_sigaus = rec.company_id.sigaus_enable and (
                not rec.fiscal_position_id or rec.fiscal_position_id.sigaus_subject
            )

    def _compute_sigaus_is_date(self):
        for rec in self:
            try:
                date = rec[rec._sigaus_secondary_unit_fields["date_field"]].date()
            except AttributeError:
                date = rec[rec._sigaus_secondary_unit_fields["date_field"]]
            rec.sigaus_is_date = (
                rec.is_sigaus and date and date >= rec.company_id.sigaus_date_from
            )

    def _compute_sigaus_has_line(self):
        for rec in self:
            rec.sigaus_has_line = any(
                line.is_sigaus
                for line in rec[rec._sigaus_secondary_unit_fields["line_ids"]]
            )

    def _compute_sigaus_company(self):
        for rec in self:
            rec.sigaus_company = rec.company_id.sigaus_enable

    def _delete_sigaus(self):
        self.filtered(
            lambda a: a.state in self._sigaus_secondary_unit_fields["editable_states"]
        ).mapped(self._sigaus_secondary_unit_fields["line_ids"]).filtered(
            lambda b: b.is_sigaus
        ).unlink()

    def _get_sigaus_line_vals(self, lines=False, **kwargs):
        self.ensure_one()
        sigaus_vals = dict()
        sigaus_product_id = self.env.ref(
            "l10n_es_sigaus_account.aportacion_sigaus_product_template"
        )
        sigaus_vals["product_id"] = sigaus_product_id.id
        kg_uom_id = self.env.ref("uom.product_uom_kgm")
        sigaus_vals[
            self[
                self._sigaus_secondary_unit_fields["line_ids"]
            ]._sigaus_secondary_unit_fields["uom_field"]
        ] = kg_uom_id.id
        date = False
        sigaus_lines = (
            lines
            if lines
            else self[self._sigaus_secondary_unit_fields["line_ids"]].filtered(
                lambda a: a.product_id and a.product_id.sigaus_has_amount
            )
        )
        if self._name == "account.move":
            # Get a default date to calculate the SIGAUS amount when the
            # SIGAUS line is newly generated
            date = self.sigaus_default_date(sigaus_lines)
        else:
            date = self[self._sigaus_secondary_unit_fields["date_field"]]
        price = self.env["l10n.es.sigaus.amount"].get_sigaus_amount(date)
        # if model isn't account.move we delete the sigaus line
        invoice_lines = []
        if self._name != "account.move":
            sigaus_line_delete = self[
                self._sigaus_secondary_unit_fields["line_ids"]
            ].filtered(lambda a: a.product_id == sigaus_product_id)
            if (
                sigaus_line_delete
                and sigaus_line_delete[
                    sigaus_line_delete._sigaus_secondary_unit_fields[
                        "invoice_lines_field"
                    ]
                ]
            ):
                invoice_lines = sigaus_line_delete[
                    sigaus_line_delete._sigaus_secondary_unit_fields[
                        "invoice_lines_field"
                    ]
                ].ids
            sigaus_line_delete.unlink()
        weight = sum(
            line[
                self[
                    self._sigaus_secondary_unit_fields["line_ids"]
                ]._sigaus_secondary_unit_fields["uom_field"]
            ]._compute_quantity(
                line[line._sigaus_secondary_unit_fields["qty_field"]],
                line.product_id.uom_id,
            )
            * line.product_id.weight
            for line in sigaus_lines
        )
        sigaus_vals.update(
            {
                self[
                    self._sigaus_secondary_unit_fields["line_ids"]
                ]._sigaus_secondary_unit_fields["qty_field"]: weight,
                "price_unit": price,
                "is_sigaus": True,
            }
        )
        if invoice_lines:
            sigaus_vals.update(
                {
                    self[
                        self._sigaus_secondary_unit_fields["line_ids"]
                    ]._sigaus_secondary_unit_fields[
                        "invoice_lines_field"
                    ]: invoice_lines
                }
            )
        if self._name == "account.move":
            sigaus_vals["move_id"] = self.id
        return sigaus_vals

    def automatic_sigaus_exception(self):
        self.ensure_one()
        products_without_weight = (
            self[self._sigaus_secondary_unit_fields["line_ids"]]
            .mapped("product_id")
            .filtered(lambda a: a.sigaus_has_amount and a.weight <= 0.0)
        )
        if products_without_weight:
            values = {
                "model": self._name,
                "origin": self.id,
                "products": products_without_weight,
            }
            note = self.env["ir.qweb"]._render(
                "l10n_es_sigaus_account.exception_sigaus", values
            )
            if not self.sigaus_automated_exception_id:
                odoobot_id = self.env.ref("base.partner_root").id
                activity = self.activity_schedule(
                    "mail.mail_activity_data_warning",
                    date.today(),
                    note=note,
                    user_id=self.user_id.id or SUPERUSER_ID,
                )
                activity.write(
                    {
                        "create_uid": odoobot_id,
                    }
                )
                self.write(
                    {
                        "sigaus_automated_exception_id": activity.id,
                    }
                )
            else:
                self.sigaus_automated_exception_id.write({"note": note})
