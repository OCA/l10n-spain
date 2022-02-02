# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.tools import ormcache


class ResCompany(models.Model):
    _inherit = "res.company"

    tbai_aeat_certificate_id = fields.Many2one(
        comodel_name="l10n.es.aeat.certificate",
        string="AEAT Certificate",
        domain="[('state', '=', 'active'), ('company_id', '=', id)]",
        copy=False,
    )
    tbai_protected_data = fields.Boolean("Protected Data", default=False)
    tbai_protected_data_txt = fields.Text(
        "Substitution Text",
        translate=True,
        default="Información protegida por el artículo 9 Reglamento 679/2016",
    )

    tbai_description_method = fields.Selection(
        string="TicketBAI Description Method",
        selection=[("auto", "Automatic"), ("fixed", "Fixed"), ("manual", "Manual")],
        default="manual",
        required=True,
        help="Method for the TicketBAI invoices description, can be one of these:\n"
        "- Automatic: the description will be the join of the invoice "
        "  lines description\n"
        "- Fixed: the description write on the below field 'TBAI "
        "  Description'\n"
        "- Manual (by default): It will be necessary to manually enter "
        "  the description on each invoice",
    )

    tbai_description = fields.Char(
        string="TicketBAI Description",
        size=250,
        help="The description for invoices. Only used when the field TicketBAI "
        "Description Method is 'Fixed'.",
    )

    @api.onchange("tbai_enabled")
    def onchange_tbai_enabled_unset_tbai_aeat_certificate_id(self):
        if not self.tbai_enabled:
            self.tbai_aeat_certificate_id = False

    def tbai_certificate_get_p12(self):
        if self.tbai_aeat_certificate_id:
            return self.tbai_aeat_certificate_id.get_p12()
        else:
            return super().tbai_certificate_get_p12()

    def tbai_certificate_get_public_key(self):
        if self.tbai_aeat_certificate_id:
            return self.tbai_aeat_certificate_id.public_key
        else:
            return None

    def tbai_certificate_get_private_key(self):
        if self.tbai_aeat_certificate_id:
            return self.tbai_aeat_certificate_id.private_key
        else:
            return None

    @ormcache("fp_template", "company")
    def _get_fp_id_from_fp_template(self, fp_template, company):
        """Low level cached search for a fiscal position given its template and
        company.
        """
        xmlids = self.env["ir.model.data"].search_read(
            [
                ("model", "=", "account.fiscal.position.template"),
                ("res_id", "=", fp_template.id),
            ],
            ["name", "module"],
        )
        return (
            xmlids
            and self.env["ir.model.data"]
            .search(
                [
                    ("model", "=", "account.fiscal.position"),
                    ("module", "=", xmlids[0]["module"]),
                    ("name", "=", "{}_{}".format(company.id, xmlids[0]["name"])),
                ]
            )
            .res_id
            or False
        )

    def get_fps_from_templates(self, fp_templates):
        """Return company fiscal positions that match the given templates."""
        self.ensure_one()
        fp_ids = []
        for tmpl in fp_templates:
            fp_id = self._get_fp_id_from_fp_template(tmpl, self)
            if fp_id:
                fp_ids.append(fp_id)
        return self.env["account.fiscal.position"].browse(fp_ids)

    def write(self, vals):
        super().write(vals)
        if vals.get("tbai_enabled", False):
            for record in self:
                if record.tbai_enabled:
                    journals = self.env["account.journal"].search([])
                    for journal in journals:
                        if "sale" == journal.type:
                            journal.sequence_id.suffix = ""
                            journal.refund_sequence = True
