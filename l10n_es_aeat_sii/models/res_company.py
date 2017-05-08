# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    @api.onchange('use_connector')
    def _check_connector_installed(self):
        module = self.env['ir.module'].search(
            [('name', '=', 'connector'), ('state', '=', 'installed')])
        if not module:
            raise exceptions.Warning(
                _('The module "Connector" is not installed. You have '
                  'to install it to activate this option'))

    sii_test = fields.Boolean(string='Test Enviroment')
    sii_version = fields.Char(
        string='SII Version', default='0.6', required=True)
    # Version 0.7 disponible pero da error en hacienda, se ha solicitado soporte
    chart_template_id = fields.Many2one(
        comodel_name='account.chart.template', string='Chart Template',
        required=True)
    use_connector = fields.Boolean(
        string='Use connector',
        help='Check it to use connector instead to send the invoice '
        'when it is validated')
    wsdl_out = fields.Char(
        string='WSDL Invoice Out', required=True,
        default='http://www.agenciatributaria.es/static_files/AEAT/'
        'Contenidos_Comunes/La_Agencia_Tributaria/Modelos_y_formularios/'
        'Suministro_inmediato_informacion/FicherosSuministros/V_06/'
        'SuministroFactEmitidas.wsdl')
    wsdl_in = fields.Char(
        string='WSDL Invoice In', required=True,
        default='http://www.agenciatributaria.es/static_files/AEAT/'
        'Contenidos_Comunes/La_Agencia_Tributaria/Modelos_y_formularios/'
        'Suministro_inmediato_informacion/FicherosSuministros/V_06/'
        'SuministroFactRecibidas.wsdl')
    wsdl_pi = fields.Char(
        string='WSDL Property Investment', required=True,
        default='http://www.agenciatributaria.es/static_files/AEAT/'
        'Contenidos_Comunes/La_Agencia_Tributaria/Modelos_y_formularios/'
        'Suministro_inmediato_informacion/FicherosSuministros/V_06/'
        'SuministroBienesInversion.wsdl')
    wsdl_ic = fields.Char(
        string='WSDL Intra-Community', required=True,
        default='http://www.agenciatributaria.es/static_files/AEAT/'
        'Contenidos_Comunes/La_Agencia_Tributaria/Modelos_y_formularios/'
        'Suministro_inmediato_informacion/FicherosSuministros/V_06/'
        'SuministroOpIntracomunitarias.wsdl')
    wsdl_pr = fields.Char(
        string='WSDL Payment Received', required=True,
        default='http://www.agenciatributaria.es/static_files/AEAT/'
        'Contenidos_Comunes/La_Agencia_Tributaria/Modelos_y_formularios/'
        'Suministro_inmediato_informacion/FicherosSuministros/V_06/'
        'SuministroCobrosEmitidas.wsdl')
    wsdl_prm = fields.Char(
        string='WSDL Money Payment Received', required=True,
        default='http://www.agenciatributaria.es/static_files/AEAT/'
        'Contenidos_Comunes/La_Agencia_Tributaria/Modelos_y_formularios/'
        'Suministro_inmediato_informacion/FicherosSuministros/V_06/'
        'SuministroCobrosMetalico.wsdl')
    wsdl_ps = fields.Char(
        string='WSDL Payment Sent', required=True,
        default='http://www.agenciatributaria.es/static_files/AEAT/'
        'Contenidos_Comunes/La_Agencia_Tributaria/Modelos_y_formularios/'
        'Suministro_inmediato_informacion/FicherosSuministros/V_06/'
        'SuministroPagosRecibidas.wsdl')
