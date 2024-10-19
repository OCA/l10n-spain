# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import _, api, exceptions, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_es_facturae_sending_code = fields.Selection(
        [("face", "FACe")], string="Sending method"
    )

    @api.constrains(
        "facturae",
        "vat",
        "country_id",
        "state_id",
        "l10n_es_facturae_sending_code",
        "organo_gestor",
        "unidad_tramitadora",
        "oficina_contable",
    )
    def _constrain_l10n_es_facturae_sending_code_face(self):
        for record in self:
            if (
                not record.l10n_es_facturae_sending_code
                or record.l10n_es_facturae_sending_code not in ["face"]
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
            if not record.organo_gestor:
                raise exceptions.ValidationError(
                    _("Organo Gestor must be defined in Spain in order to send to FACe")
                )
            if not record.unidad_tramitadora:
                raise exceptions.ValidationError(
                    _(
                        "Unidad Tramitadora must be defined in Spain in order to send to FACe"
                    )
                )
            if not record.oficina_contable:
                raise exceptions.ValidationError(
                    _(
                        "Oficina Contable must be defined in Spain in order to send to FACe"
                    )
                )

    def _get_facturae_backend(self):
        return self.env.ref("l10n_es_facturae_face.face_backend")

    def _get_facturae_exchange_type(self):
        return self.env.ref("l10n_es_facturae_face.facturae_exchange_type")
