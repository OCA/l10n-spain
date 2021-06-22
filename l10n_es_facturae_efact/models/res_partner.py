# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import _, api, exceptions, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_es_facturae_sending_code = fields.Selection(
        selection_add=[("efact", "e.Fact")]
    )
    facturae_efact_code = fields.Char(string="e.Fact code")

    @api.constrains(
        "facturae",
        "vat",
        "country_id",
        "state_id",
        "l10n_es_facturae_sending_code",
        "facturae_efact_code",
    )
    def constrain_efact(self):
        for record in self:
            if record.l10n_es_facturae_sending_code != "efact":
                continue
            if not record.facturae:
                raise exceptions.ValidationError(
                    _("Facturae must be selected in order to send to e.Fact")
                )
            if not record.vat:
                raise exceptions.ValidationError(
                    _("Vat must be defined in order to send to e.Fact")
                )
            if not record.country_id:
                raise exceptions.ValidationError(
                    _("Country must be defined in order to send to e.Fact")
                )
            if record.country_id.code_alpha3 == "ESP":
                if not record.state_id:
                    raise exceptions.ValidationError(
                        _(
                            "State must be defined in Spain in order to "
                            "send to e.Fact"
                        )
                    )
            if not record.facturae_efact_code or len(record.facturae_efact_code) != 22:
                raise exceptions.ValidationError(
                    _("e.Fact code must be correctly defined")
                )
