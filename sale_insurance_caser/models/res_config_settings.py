# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    caser_is_production = fields.Boolean(
        string="Caser Production Environment",
        config_parameter="sale_insurance_caser.is_production",
        help="Use production Caser endpoint. If unchecked uses testing.",
    )
    caser_username = fields.Char(
        string="Caser Web Username",
        config_parameter="sale_insurance_caser.username",
        help="Username for Caser SOAP service authentication",
    )
    caser_agency_code = fields.Char(
        config_parameter="sale_insurance_caser.agency_code",
        help="Agency code provided by Caser",
    )
    caser_agent_code = fields.Char(
        config_parameter="sale_insurance_caser.agent_code",
        help="Agent code provided by Caser",
    )
    caser_sica_code = fields.Char(
        string="Caser SICA Code",
        config_parameter="sale_insurance_caser.sica_code",
        help="SICA code provided by Caser",
    )

    def action_open_caser_price_ranges(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Caser Price Ranges",
            "res_model": "caser.price.range",
            "view_mode": "list",
        }
