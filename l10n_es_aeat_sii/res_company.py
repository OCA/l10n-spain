# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import openerp.exceptions
from openerp.osv import fields, osv, orm

class res_company(osv.osv):
     _inherit = 'res.company'

     def _check_connector_installed(cr, uid, ids):
        module = self.env['ir.module'].search(
            [('name', '=', 'connector'), ('state', '=', 'installed')])
        if not module:
            raise exceptions.Warning(
                _('The module "Connector" is not installed. You have '
                  'to install it to activate this option'))


     _columns = {
       'sii_test': fields.boolean('Test Enviroment'),
       'use_connector': fields.boolean('Use connector', help='Check it to use connector instead to send the invoice when it is validated'),
       'wsdl_out': fields.char('WSDL Invoice Out'),
       'wsdl_in': fields.char('WSDL Invoice In'),
       'wsdl_pi': fields.char('WSDL Property Investment'),
       'wsdl_ic': fields.char('WSDL Intra-Community'),
       'wsdl_pr': fields.char('WSDL Payment Received'),
       'wsdl_prm': fields.char('WSDL Money Payment Received'),
       'wsdl_ps': fields.char('WSDL Payment Sent'),
       'version_sii': fields.char('Versión SII AEAT'),
     }

     _defaults = {
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
       'wsdl_prm' : 'http://www.agenciatributaria.es/static_files/AEAT/'
        'Contenidos_Comunes/La_Agencia_Tributaria/Modelos_y_formularios/'
        'Suministro_inmediato_informacion/FicherosSuministros/V_06/'
        'SuministroOpTrascendTribu.wsdl',
       'wsdl_ps': 'http://www.agenciatributaria.es/static_files/AEAT/'
        'Contenidos_Comunes/La_Agencia_Tributaria/Modelos_y_formularios/'
        'Suministro_inmediato_informacion/FicherosSuministros/V_06/'
        'SuministroPagosRecibidas.wsdl',
       'version_sii': 0.6,
     }
res_company()
