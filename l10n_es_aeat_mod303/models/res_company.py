# Copyright 2024 Moduon Team - Emilio Pascual

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    main_activity_code_id = fields.Many2one(
        comodel_name="l10n.es.aeat.mod303.report.activity.code",
        string="Código actividad principal",
    )
    main_activity_iae = fields.Char(
        string="Epígrafe I.A.E. actividad principal",
        size=4,
    )
    other_first_activity_code_id = fields.Many2one(
        comodel_name="l10n.es.aeat.mod303.report.activity.code",
        string="Código 1ª actividad",
    )
    other_first_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 1ª actividad",
        size=4,
    )
    other_second_activity_code_id = fields.Many2one(
        comodel_name="l10n.es.aeat.mod303.report.activity.code",
        string="Código 2ª actividad",
    )
    other_second_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 2ª actividad",
        size=4,
    )
    other_third_activity_code_id = fields.Many2one(
        comodel_name="l10n.es.aeat.mod303.report.activity.code",
        string="Código 3ª actividad",
    )
    other_third_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 3ª actividad",
        size=4,
    )
    other_fourth_activity_code_id = fields.Many2one(
        comodel_name="l10n.es.aeat.mod303.report.activity.code",
        string="Código 4ª actividad",
    )
    other_fourth_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 4ª actividad",
        size=4,
    )
    other_fifth_activity_code_id = fields.Many2one(
        comodel_name="l10n.es.aeat.mod303.report.activity.code",
        string="Código 5ª actividad",
    )
    other_fifth_activity_iae = fields.Char(
        string="Epígrafe I.A.E. 5ª actividad",
        size=4,
    )
