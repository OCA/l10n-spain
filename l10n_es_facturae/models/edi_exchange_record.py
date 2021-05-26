# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class EdiExchangeRecord(models.Model):

    _inherit = "edi.exchange.record"

    l10n_es_facturae_status = fields.Selection(
        selection=lambda r: r.env["account.move"]
        ._fields["l10n_es_facturae_status"]
        .selection,
        readonly=True,
        string="Facturae State",
    )
    l10n_es_facturae_cancellation_status = fields.Selection(
        selection=lambda r: r.env["account.move"]
        ._fields["l10n_es_facturae_cancellation_status"]
        .selection,
        readonly=True,
        string="Facturae Cancellation state",
    )
    l10n_es_facturae_motive = fields.Text(
        string="Facturae description",
        readonly=True,
    )
    l10n_es_facturae_cancellation_motive = fields.Text(
        readonly=True, string="Facturae Cancellation motive"
    )
