# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class L10nEsAtcSiiArt25Detail(models.Model):
    """Operation exempt by art. 25 of Law 19/1994 (investments of the Canary
    Islands Investment Reserve) of an invoice, which the SII of the Canary tax
    agency wants in the `DatosArticulo25` block of the key 19 of the issued
    invoices and the key 17 of the received ones."""

    _name = "l10n.es.atc.sii.art25.detail"
    _description = "Art. 25 Law 19/1994 detail of the Canary SII"
    _order = "sequence, id"

    move_id = fields.Many2one(
        comodel_name="account.move",
        required=True,
        index=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(default=10)
    advance_payment = fields.Boolean(
        help="The invoice is an advance payment of the operation.",
    )
    asset_type = fields.Selection(
        selection=[
            ("01", "Acquisition, delivery or construction of real estate"),
            ("02", "Acquisition, delivery or construction of movable goods"),
            ("03", "Right of use of industrial or intellectual property"),
            ("04", "Right of use of unpatented know-how"),
            ("05", "Administrative concessions"),
        ],
        required=True,
    )
    document_type = fields.Selection(
        selection=[("01", "Notarial"), ("02", "Private"), ("03", "Other")],
        help="Document in which the exempt operation is recorded, required for "
        "the real estate.",
    )
    protocol_number = fields.Char(
        size=6,
        help="Protocol number of the notarial deed of the operation.",
    )
    notary_name = fields.Char(
        string="Notary",
        size=120,
        help="Surnames and name of the notary who recorded the operation.",
    )

    @api.constrains("asset_type", "document_type", "protocol_number", "notary_name")
    def _check_document(self):
        """What the ATC requires of the document of the real estate."""
        for detail in self.filtered(lambda detail: detail.asset_type == "01"):
            if not detail.document_type:
                raise ValidationError(
                    self.env._(
                        "The art. 25 operations on real estate need the type of "
                        "the document in which they are recorded."
                    )
                )
            if detail.document_type == "01" and not (
                detail.protocol_number and detail.notary_name
            ):
                raise ValidationError(
                    self.env._(
                        "A notarial deed of an art. 25 operation on real estate "
                        "needs its protocol number and notary."
                    )
                )

    def _get_sii_dict(self):
        """`DetalleArticulo25` of the details."""
        details = []
        for detail in self:
            vals = {
                "PagoAnticipadoArt25": "S" if detail.advance_payment else "N",
                "TipoBienArt25": detail.asset_type,
            }
            if detail.document_type:
                document = {"TipoDocumArt25": detail.document_type}
                if detail.protocol_number:
                    document["NumeroProtocolo"] = detail.protocol_number
                if detail.notary_name:
                    document["ApellidosNombreNotario"] = detail.notary_name
                vals["IDDocumentoArt25"] = [document]
            details.append(vals)
        return details
