
from odoo import models, fields


class AeatStateCodeMappings(models.Model):
    _name = 'aeat.state.code.mapping'
    _description = 'Aeat State code Mappings'

    state_code = fields.Char(string='Code', required=True, size=3)
    aeat_code = fields.Char(string='AEAT Code', required=True, size=2)
