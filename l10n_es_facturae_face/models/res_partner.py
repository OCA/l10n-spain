# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import _, api, exceptions, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_es_facturae_sending_code = fields.Selection(
        [("face", "FACe")], string="Sending method"
    )
    # TODO: Replace this by a boolean on 15.0. We are keeping this on 13 and 14 because
    #  migration might be problematic

    @api.constrains(
        "facturae",
        "vat",
        "country_id",
        "state_id",
        "l10n_es_facturae_sending_code",
    )
    def _constrain_l10n_es_facturae_sending_code_face(self):
        for record in self:
            if (
                not record.l10n_es_facturae_sending_code
                or record.l10n_es_facturae_sending_code != "face"
            ):
                continue
            if not record.facturae:
                raise exceptions.ValidationError(
                    _("Facturae must be selected in order to send to FACe")
                )
            if not record.vat:
                raise exceptions.ValidationError(
                    _("Vat must be defined in order to send to FACe")
                )
            if not record.country_id:
                raise exceptions.ValidationError(
                    _("Country must be defined in order to send to FACe")
                )
            if record.country_id.code_alpha3 == "ESP":
                if not record.state_id:
                    raise exceptions.ValidationError(
                        _("State must be defined in Spain in order to send to FACe")
                    )
