# -*- encoding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class InformacionCatastral(models.Model):
    _name = 'informacion.catastral'
    _description = 'Información Catastral'
    _rec_name = "display_name"


    cod_postal = fields.Many2one('res.city.zip', string="Código postal", required=True)
    cod_provincia = fields.Integer(string="Código provincia")
    municipio = fields.Many2one('res.country.state', string="Municipio", required=True)
    situacion_inmueble = fields.Selection([('1', '01'), ('2', '02'), ('3', '03'), ('4', '04')], required=True)
    referencia_catastral = fields.Char(string="Referencia catastral")
    tipo_via = fields.Text(string="Tipo de vía", required=True)
    nombre_via_publica = fields.Text("Nombre vía pública", required=True)
    tipo_numeracion = fields.Char(string="Tipo numeración", default=0)
    num_casa = fields.Integer(string="Número de casa", default=0)
    calificador_numero = fields.Integer(string="Calficador del número", default=0, required=True)
    bloque = fields.Text(string="Bloque")
    partner_id = fields.Many2one('res.partner')
    display_name = fields.Char(compute='_compute_new_display_name', store=True, index=True)

    @api.depends('tipo_via', 'nombre_via_publica', 'cod_postal')
    def _compute_new_display_name(self):
        for rec in self:
            name = [rec.tipo_via + ' ' + rec.nombre_via_publica]
            if rec.cod_postal:
                name.append(rec.cod_postal.name_get()[0][1])
            rec.display_name = ", ".join(name)

    @api.onchange('cod_postal','referencia_catastral')
    def _onchange_cod_postal(self):
        for info in self:
            if info.cod_postal:
                # Codigo provincia
                info.cod_provincia = info.cod_postal.name[:2]
                # Municipio
                info.municipio = info.cod_postal.city_id.state_id
                # Situacion inmueble
                if not info.referencia_catastral:
                    info.situacion_inmueble = '4'
                elif info.municipio and info.municipio.code and info.municipio.code not in ['NA', 'BI', 'SS', 'VI']:
                    info.situacion_inmueble = '1'
                elif info.municipio and info.municipio.code and info.municipio.code in ['BI', 'SS', 'VI']:
                    info.situacion_inmueble = '2'
                elif info.municipio and info.municipio.code and info.municipio.code == 'NA':
                    info.situacion_inmueble = '3'

