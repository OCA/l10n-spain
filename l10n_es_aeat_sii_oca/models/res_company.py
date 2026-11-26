# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2017 Studio73 - Pablo Fuentes <pablo@studio73.es>
# Copyright 2017 Studio73 - Jordi Tolsà <jordi@studio73.es>
# Copyright 2018 Javi Melendez <javimelex@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import UTC, datetime, timedelta

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _l10n_es_regime_available_codes(self, use, applicability=None):
        codes = super()._l10n_es_regime_available_codes(
            use, applicability=applicability
        )
        if self.sii_enabled and use in ("sale", "purchase") and "06" not in codes:
            codes = list(codes) + ["06"]
        return codes

    def _get_sii_default_regime_code(self):
        """Registration key of the lines whose taxes have no regime code.

        The special VAT regime of the company only gives an SII key for the
        cash basis criterion: the codes of the other regimes are VERI*FACTU ones.
        """
        self.ensure_one()
        return "07" if self.l10n_es_special_vat_regime == "cash_basis" else "01"

    sii_enabled = fields.Boolean(string="Enable SII")
    sii_test = fields.Boolean(string="Is it the SII test environment?")
    sii_description_method = fields.Selection(
        string="SII Description Method",
        selection=[("auto", "Automatic"), ("fixed", "Fixed"), ("manual", "Manual")],
        default="manual",
        help="Method for the SII invoices description, can be one of these:\n"
        "- Automatic: the description will be the join of the invoice "
        "  lines description\n"
        "- Fixed: the description write on the below field 'SII "
        "  Description'\n"
        "- Manual (by default): It will be necessary to manually enter "
        "  the description on each invoice\n\n"
        "For all the options you can append a header text using the "
        "below fields 'SII Sale header' and 'SII Purchase header'",
    )
    sii_description = fields.Char(
        string="SII Description",
        size=500,
        help="The description for invoices. Only used when the field SII "
        "Description Method is 'Fixed'.",
    )
    sii_header_customer = fields.Char(
        string="SII Customer header",
        size=500,
        help="An optional header description for customer invoices. "
        "Applied on all the SII description methods",
    )
    sii_header_supplier = fields.Char(
        string="SII Supplier header",
        size=500,
        help="An optional header description for supplier invoices. "
        "Applied on all the SII description methods",
    )
    sii_method = fields.Selection(
        string="Method",
        selection=[("auto", "Automatic"), ("manual", "Manual")],
        default="auto",
        help="By default, the invoice is sent/queued in validation process. "
        "With manual method, there's a button to send the invoice.",
    )
    sii_start_date = fields.Date(
        help="If this field is set, the sii won't be enabled on invoices with lower "
        "invoice date. If not set, the sii can be enabled on all invoice dates"
    )

    send_mode = fields.Selection(
        selection=[
            ("auto", "On validate"),
            ("fixed", "At fixed time"),
            ("delayed", "With delay"),
        ],
        default="delayed",
    )
    sent_time = fields.Float()
    delay_time = fields.Float()
    sii_period = fields.Selection(
        selection=[
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
        ],
        default="monthly",
    )

    def _get_sii_sending_time(self):
        if self.send_mode == "fixed":
            # The time is the one of the user's timezone (UTC by default)
            now = datetime.now(self.env.tz).replace(second=0, microsecond=0)
            send_time = now.replace(hour=0, minute=0) + timedelta(
                minutes=round(self.sent_time * 60)
            )
            if send_time < now:
                send_time += timedelta(days=1)
            # Naive UTC, as the dates of the jobs
            return send_time.astimezone(UTC).replace(tzinfo=None)
        else:
            delay_time = (
                0.0
                if self.send_mode == "auto" or not self.delay_time
                else self.delay_time
            )
            return fields.Datetime.now() + timedelta(hours=delay_time)
