# -*- coding: utf-8 -*-
# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.osv import osv, fields
from openerp import exceptions
from openerp.tools.translate import _


class ResCompany(osv.Model):
    _inherit = 'res.company'

    def _check_connector_installed(self, cr, uid, ids):
        module = self.env['ir.module'].search(cr, uid, [('name', '=', 'connector'), ('state', '=', 'installed')])
        if not module:
            raise exceptions.Warning(
                _('The module "Connector" is not installed. You have '
                  'to install it to activate this option'))

    _columns = {
        'sii_test': fields.boolean(string='Test Enviroment'),
        'sii_version': fields.char(string='SII Version', size=8),
        'use_connector': fields.boolean(
            string='Use connector',
            help='Check it to use connector instead to send the invoice '
                 'when it is validated', readonly=True),
        'wsdl_out': fields.char(
            string='WSDL Invoice Out', size=256),
        'wsdl_in': fields.char(
            string='WSDL Invoice In', size=256),
        'wsdl_pi': fields.char(
            string='WSDL Property Investment', size=256),
        'wsdl_ic': fields.char(
            string='WSDL Intra-Community', size=256),
        'wsdl_pr': fields.char(
            string='WSDL Payment Received', size=256),
        'wsdl_prm': fields.char(
            string='WSDL Money Payment Received', size=256),
        'wsdl_ps': fields.char(
            string='WSDL Payment Sent', size=256),
    }

    _defaults = {
        'sii_version': '0.6',
        'wsdl_out': 'http://www.agenciatributaria.es/static_files/AEAT/'
                    'Contenidos_Comunes/La_Agencia_Tributaria/Modelos_y_formularios/'
                    'Suministro_inmediato_informacion/FicherosSuministros/V_06/'
                    'SuministroFactEmitidas.wsdl',
        'wsdl_in': 'http://www.agenciatributaria.es/static_files/AEAT/'
                   'Contenidos_Comunes/La_Agencia_Tributaria/Modelos_y_formularios/'
                   'Suministro_inmediato_informacion/FicherosSuministros/V_06/'
                   'SuministroFactRecibidas.wsdl',
        'wsdl_pi': 'http://www.agenciatributaria.es/static_files/AEAT/'
                   'Contenidos_Comunes/La_Agencia_Tributaria/Modelos_y_formularios/'
                   'Suministro_inmediato_informacion/FicherosSuministros/V_06/'
                   'SuministroBienesInversion.wsdl',
        'wsdl_ic': 'http://www.agenciatributaria.es/static_files/AEAT/'
                   'Contenidos_Comunes/La_Agencia_Tributaria/Modelos_y_formularios/'
                   'Suministro_inmediato_informacion/FicherosSuministros/V_06/'
                   'SuministroOpIntracomunitarias.wsdl',
        'wsdl_pr': 'http://www.agenciatributaria.es/static_files/AEAT/'
                   'Contenidos_Comunes/La_Agencia_Tributaria/Modelos_y_formularios/'
                   'Suministro_inmediato_informacion/FicherosSuministros/V_06/'
                   'SuministroCobrosEmitidas.wsdl',
        'wsdl_prm': 'http://www.agenciatributaria.es/static_files/AEAT/'
                    'Contenidos_Comunes/La_Agencia_Tributaria/Modelos_y_formularios/'
                    'Suministro_inmediato_informacion/FicherosSuministros/V_06/'
                    'SuministroCobrosMetalico.wsdl',
        'wsdl_ps': 'http://www.agenciatributaria.es/static_files/AEAT/'
                   'Contenidos_Comunes/La_Agencia_Tributaria/Modelos_y_formularios/'
                   'Suministro_inmediato_informacion/FicherosSuministros/V_06/'
                   'SuministroPagosRecibidas.wsdl'

    }
