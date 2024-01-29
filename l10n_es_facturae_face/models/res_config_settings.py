# Copyright 2024 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = "res.config.settings"

    face_wsdl = fields.Selection(
        [
            ("https://se-face-webservice.redsara.es/facturasspp2?wsdl", "Development"),
            ("https://webservice.face.gob.es/facturasspp2?wsdl", "Production"),
        ],
        config_parameter="facturae.face.ws",
        string="FACe environment",
    )
    face_certificate_filename = fields.Char(
        compute="_compute_face_certificate",
        inverse="_inverse_face_certificate_filename",
    )
    face_certificate = fields.Binary(
        compute="_compute_face_certificate",
        inverse="_inverse_face_certificate",
        readonly=False,
        string="FACe certificate",
    )

    @api.depends("company_id")
    def _compute_face_certificate(self):
        file = self.env.ref("l10n_es_facturae_face.face_certificate")
        for record in self:
            record.face_certificate = file.datas
            record.face_certificate_filename = file.name

    def _inverse_face_certificate(self):
        for record in self:
            self.env.ref(
                "l10n_es_facturae_face.face_certificate"
            ).datas = record.face_certificate

    def _inverse_face_certificate_filename(self):
        for record in self:
            self.env.ref(
                "l10n_es_facturae_face.face_certificate"
            ).name = record.face_certificate_filename
