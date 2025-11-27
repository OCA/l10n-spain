# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class IneCode(models.Model):
    _name = "res.ine.code"
    _description = "Codes for cities in the INE (Spanish Statistics National Institute)"
    _rec_name = "city_name"

    ine_code_state = fields.Char(string="State INE code")
    ine_code_province = fields.Integer(string="Province INE code")
    ine_code_city = fields.Integer(string="City INE code")
    city_name = fields.Char(string="City")
    city_name_simplified = fields.Char(string="City simplified")
    city_name_aka = fields.Char(string="City alternative name")
    city_name_aka_simplified = fields.Char(string="City alternative name simplified")
    city_name_reordered = fields.Char(string="City reordered name")
    city_name_reordered_simplified = fields.Char(
        string="City reordered name simplified"
    )
    city_id = fields.Many2one(
        comodel_name="res.city",
        string="Linked City",
        help="Link to the city in base_location",
    )
    state_id = fields.Many2one(
        comodel_name="res.country.state",
        string="Province",
        related="city_id.state_id",
        store=True,
        help="Province obtained from the linked city",
    )

    def name_get(self):
        """Display full INE code: CCAA + Province + City."""
        result = []
        for record in self:
            if (
                record.ine_code_state
                and record.ine_code_province
                and record.ine_code_city
            ):
                # Format: "CCAAProvinceCity" e.g. "1328079" for Madrid
                state_code = str(record.ine_code_state).zfill(2)
                province_code = str(record.ine_code_province).zfill(2)
                city_code = str(record.ine_code_city).zfill(3)
                name = f"{state_code}{province_code}{city_code}"
            else:
                # If codes not available, show city name as fallback
                name = record.city_name or ""
            result.append((record.id, name))
        return result

    def _name_search(
        self, name="", args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        """Enhanced search to find cities by any name variant."""
        args = args or []
        if name:
            # Search in all name fields for better user experience
            domain = [
                "|",
                "|",
                "|",
                "|",
                "|",
                ("city_name", operator, name),
                ("city_name_simplified", operator, name),
                ("city_name_aka", operator, name),
                ("city_name_aka_simplified", operator, name),
                ("city_name_reordered", operator, name),
                ("city_name_reordered_simplified", operator, name),
            ]
            return self._search(
                domain + args, limit=limit, access_rights_uid=name_get_uid
            )
        return super()._name_search(
            name=name,
            args=args,
            operator=operator,
            limit=limit,
            name_get_uid=name_get_uid,
        )

    @api.model
    def read_group(
        self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True
    ):
        if "ine_code_state" in groupby and "ine_code_province" in groupby:
            fields_to_remove = ["ine_code_city"]
        elif "ine_code_state" in groupby:
            fields_to_remove = ["ine_code_province", "ine_code_city"]
        elif "ine_code_province" in groupby:
            fields_to_remove = ["ine_code_state", "ine_code_city"]
        else:
            fields_to_remove = []
        for field_to_remove in fields_to_remove:
            if field_to_remove in fields:
                fields.remove(field_to_remove)
        return super().read_group(domain, fields, groupby, offset, limit, orderby, lazy)
