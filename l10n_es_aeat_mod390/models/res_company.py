# Copyright 2024 Moduon Team - Emilio Pascual

from odoo import _, fields, models

REPRESENTATIVE_HELP = _("Nombre y apellidos del representante")
NOTARY_CODE_HELP = _(
    "Código de la notaría en la que se concedió el poder de representación "
    "para esta persona."
)


class ResCompany(models.Model):
    _inherit = "res.company"

    main_activity = fields.Char(
        string="Actividad principal",
        size=40,
    )
    other_first_activity = fields.Char(
        string="1ª actividad",
        size=40,
    )
    other_second_activity = fields.Char(
        string="2ª actividad",
        size=40,
    )
    other_third_activity = fields.Char(
        string="3ª actividad",
        size=40,
    )
    other_fourth_activity = fields.Char(
        string="4ª actividad",
        size=40,
    )
    other_fifth_activity = fields.Char(
        string="5ª actividad",
        size=40,
    )
    first_representative_name = fields.Char(
        string="Nombre del primer representante",
        size=80,
        help=REPRESENTATIVE_HELP,
    )
    first_representative_vat = fields.Char(
        string="NIF del primer representante",
        size=9,
    )
    first_representative_date = fields.Date(
        string="Fecha poder del primer representante",
    )
    first_representative_notary = fields.Char(
        string="Notaría del primer representante",
        size=12,
        help=NOTARY_CODE_HELP,
    )
    second_representative_name = fields.Char(
        string="Nombre del segundo representante",
        size=80,
        help=REPRESENTATIVE_HELP,
    )
    second_representative_vat = fields.Char(
        string="NIF del segundo representante",
        size=9,
    )
    second_representative_date = fields.Date(
        string="Fecha poder del segundo representante",
    )
    second_representative_notary = fields.Char(
        string="Notaría del segundo representante",
        size=12,
        help=NOTARY_CODE_HELP,
    )
    third_representative_name = fields.Char(
        string="Nombre del tercer representante",
        size=80,
        help=REPRESENTATIVE_HELP,
    )
    third_representative_vat = fields.Char(
        string="NIF del tercer representante",
        size=9,
    )
    third_representative_date = fields.Date(
        string="Fecha poder del tercer representante",
    )
    third_representative_notary = fields.Char(
        string="Notaría del tercer representante",
        size=12,
        help=NOTARY_CODE_HELP,
    )
