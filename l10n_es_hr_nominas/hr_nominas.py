# -*- encoding: utf-8 -*-
##############################################################################
#
#    AvanzOSC, Avanzed Open Source Consulting 
#    Copyright (C) 2009 Ting! (<http://www.ting.es>). All Rights Reserved
#    Copyright (c) 2010 Acysos S.L. (http://acysos.com) All Rights Reserved.
#                       Update to OpenERP 6.0 Ignacio Ibeas <ignacio@acysos.com> 
#    Copyright (C) 2011-2012 Iker Coranti (www.avanzosc.com). All Rights Reserved
#                       Update to OpenERP 6.1 Iker Coranti
#
#    
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
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from osv import osv
from osv import fields
import time
import datetime
import pooler
from tools.translate import _

class res_company(osv.osv):
    _name = 'res.company'
    _inherit = 'res.company'
    _columns = {
        'diario_destino': fields.many2one('account.journal', 'Diario de Destino', required=True),         
        'cuenta_ss_empresa': fields.many2one('account.account', 'Cuenta Seguridad Social a cargo de la empresa', required=True),
        'cuenta_ss_acreedores': fields.many2one('account.account', 'Cuenta Organismos de la S.S acreedores', required=True),
        'cuenta_hacienda_publica': fields.many2one('account.account', 'Cuenta H.P acreedor por retenciones practicadas', required=True),
        'cuenta_pendientes_pago': fields.many2one('account.account', 'Cuenta Remuneraciones pendientes de pago', required=True),
        'cuenta_bancos': fields.many2one('account.account', 'Cuenta Bancos e instituciones de crédito', required=True),
        'cuenta_anticipos': fields.many2one('account.account', 'Cuenta anticipos de remuneraciones', required=True),
            }

res_company()

def get_configuration(cr, uid, ids, context=None):
    #############################################
    # OBJETOS #
    #############################################
    pool = pooler.get_pool(cr.dbname)
    user_obj = pool.get('res.users')
    company_obj = pool.get('res.company')
    #############################################

    obj_user = user_obj.browse(cr, uid, uid)
    cp=obj_user.company_id
    print cp
    obj_company = company_obj.browse(cr, uid, obj_user.company_id.id)
    res = {}
    if obj_company.cuenta_ss_empresa:
        #Como las cuentas son obligatorias si esta definida esta cuenta estarán todas definidas
        res['diario_destino'] = obj_company.diario_destino.id
        res['cuenta_ss_empresa'] = obj_company.cuenta_ss_empresa.id
        res['cuenta_ss_acreedores'] = obj_company.cuenta_ss_acreedores.id
        res['cuenta_hacienda_publica'] = obj_company.cuenta_hacienda_publica.id
        res['cuenta_pendientes_pago'] = obj_company.cuenta_pendientes_pago.id
        res['cuenta_bancos'] = obj_company.cuenta_bancos.id
        res['cuenta_anticipos'] = obj_company.cuenta_anticipos.id            
        return res
    else:
        company_name = str(obj_user.company_id.name)
        raise osv.except_osv(_('No hay una configuración de cuentas activa para la compañia ') + company_name, _('Debe configurar las cuentas!\nPor favor configure las cuentas en el menú de configuración de la compañia: ') + company_name)

class hr_employee(osv.osv):
    _name = 'hr.employee'
    _inherit = 'hr.employee'
    _columns = {
      'retribucion_bruta': fields.float('Retribución Bruta', digits=(16, 2)),
      'ss_empresa': fields.float('S.S a Cargo de la empresa', digits=(16, 2)),
      'ss_trabajador': fields.float('S.S a cargo del Trabajador', digits=(16, 2)),
      'irpf': fields.float('Retención IRPF (%)', digits=(16, 2)),
      'retribucion_bruta_extra': fields.float('Retribución Bruta', digits=(16, 2)),
      'ss_empresa_extra': fields.float('S.S a Cargo de la empresa', digits=(16, 2)),
      'ss_trabajador_extra': fields.float('S.S a cargo del Trabajador', digits=(16, 2)),
      'irpf_extra': fields.float('Retención IRPF (%)', digits=(16, 2)),
      'nominas_ids': fields.one2many('hr.nomina', 'employee_id', 'Nóminas del Empleado', readonly=True),
      'anticipos_ids': fields.one2many('hr.anticipo', 'employee_id', 'Anticipos del Empleado', readonly=True),
      'cuenta_id': fields.many2one('account.account', 'Cuenta', required=True, help="El empleado debe tener una cuenta para su nómina."),
    }
    _defaults = {
        'cuenta_id': lambda * a: 377 or None,
    }
   
hr_employee()

class hr_nomina(osv.osv):
    _name = 'hr.nomina'
    _description = 'Nominas de Empleados'
    _columns = {
       'name': fields.char('Nómina', size=20),
       'employee_id': fields.many2one('hr.employee', 'Empleado', required=True, select="1"),
       'retribucion_bruta': fields.float('Retribución Bruta', digits=(16, 2)),
       'ss_empresa': fields.float('S.S a Cargo de la empresa', digits=(16, 2)),
       'ss_trabajador': fields.float('S.S a cargo del Trabajador', digits=(16, 2)),
       'irpf': fields.float('Retención IRPF (%)', digits=(16, 2)),
       'fecha_nomina': fields.date('Fecha de la Nómina', select="1"),
       'state': fields.selection((('borrador', 'Borrador'),
                                  ('confirmada', 'Confirmada'),
                                  ('pagada', 'Pagada'),
                                  ('cancelada', 'Cancelada')), 'Estado Nómina', readonly=True, select="1"),
       'numero': fields.char('Número de nomina', size=32, readonly=True, help="Número único de nómina, se asigna automáticamente cuando se crea la nómina", select="1"),
       'extra': fields.boolean('Paga Extra'),
       'asiento_nomina_confirmada': fields.many2one('account.move', 'Asiento Nómina confirmada', readonly=True),
       'asiento_nomina_pagada': fields.many2one('account.move', 'Asiento Nómina pagada', readonly=True),
    }

    _defaults = {
        'state': lambda * a:'borrador',
    }

    def comprueba_mes(self, fecha_anticipo, fecha_nomina):
        anticipo = time.strptime(fecha_anticipo, '%Y-%m-%d')
        nomina = time.strptime(fecha_nomina, '%Y-%m-%d')
        dateNomina = datetime.datetime(nomina[0], nomina[1], nomina[2])
        dateAnterior = time.strptime((dateNomina - datetime.timedelta(nomina[2] + 1)).strftime('%Y-%m-%d'), '%Y-%m-%d')

        if (anticipo[0] == dateAnterior[0]) and (dateAnterior[1] == anticipo[1]): #Si se solicito anticipo el mes pasado
            return True
        else:
            return False

    def comprueba_anticipo(self, cr, uid, ids, fechaNomina, empleado_id):
        ################################################################
        # OBJETOS
        ################################################################
        anticipo_obj = self.pool.get('hr.anticipo')
        ################################################################
        anticipo_ids = anticipo_obj.search(cr, uid, [('employee_id', '=', empleado_id)])
        for anticipo in anticipo_ids:
            obj_anticipo = anticipo_obj.browse(cr, uid, anticipo)
            if self.comprueba_mes(obj_anticipo.fecha_anticipo, fechaNomina) and obj_anticipo.state == 'pagado':
                return obj_anticipo.cantidad
        
        return 0

    def confirmar_nomina(self, cr, uid, ids, *args):
        ##################################################################
        # OBJETOS
        ##################################################################
        account_journal_obj = self.pool.get('account.journal')
        account_period_obj = self.pool.get('account.period')
        account_move_obj = self.pool.get('account.move')
        account_move_line_obj = self.pool.get('account.move.line')
        ##################################################################
        cuentas = get_configuration(cr, uid, ids)
        for nom in self.browse(cr, uid, ids):
            if nom.state != 'borrador':
                continue
            journal_id = cuentas['diario_destino']
            numero = self.pool.get('ir.sequence').get(cr, uid, 'hr.nomina')
            journal = account_journal_obj.browse(cr, uid, journal_id)
            fechaNomina = nom.fecha_nomina
            line = {}

            period_ids = account_period_obj.search(cr, uid, [('date_start', '<=', fechaNomina or time.strftime('%Y-%m-%d')), ('date_stop', '>=', fechaNomina or time.strftime('%Y-%m-%d'))])
            if len(period_ids):
                periodo_id = period_ids[0]
            else:
                raise osv.except_osv(_('No existe un periodo para esa fecha de nomina!'), _('No se pueden generar nóminas cuya fecha esté en un periodo que no existe, \nsi desea generarla por favor cree el periodo contable correspondiente.'))

            referencia = numero + ' : ' + nom.employee_id.name + ' - ' + fechaNomina
            if nom.extra:
                referencia = "Paga Extra: " + nom.employee_id.name + ' - ' + fechaNomina
            move_val = {
                    'ref': referencia, 
                    'journal_id': journal_id, 
                    'date': fechaNomina, 
                    'period_id': periodo_id,
                    }

            move_id = account_move_obj.create(cr, uid, move_val)

            #Cuenta del empleado
            cuenta_id = nom.employee_id.cuenta_id.id
            #si no tiene cuenta lanzamos un error
            if not cuenta_id:
                raise osv.except_osv(_('No existe una cuenta configurada para el empleado!'), _('Por favor configure una cuenta en la ficha del empleado en la que generar los asientos de la nómina.'))
            retencion_irpf = (nom.retribucion_bruta * nom.irpf) / 100
            anticipo = self.comprueba_anticipo(cr, uid, ids, fechaNomina, nom.employee_id.id)

            sueldo_neto = nom.retribucion_bruta - retencion_irpf - nom.ss_trabajador
            if anticipo and nom.extra == False:
                sueldo_neto -= anticipo
                val ={
                      'account_id': cuentas['cuenta_anticipos'], 
                      'move_id': move_id,
                      'journal_id': journal_id, 
                      'period_id': periodo_id, 
                      'name': 'Anticipo', 
                      'credit': anticipo, 
                      'ref': referencia
                      }
                account_move_line_obj.create(cr, uid, val)
            
            account = {
                      'account_id': cuenta_id, 
                      'move_id': move_id, 
                      'journal_id': journal_id, 
                      'period_id': periodo_id, 
                      'name': 'Sueldo Bruto', 
                      'debit': nom.retribucion_bruta , 
                      'ref': referencia 
                      }  
            account_move_line_obj.create(cr, uid, account)
            
            ss_empresa = {
                       'account_id': cuentas['cuenta_ss_empresa'], 
                       'move_id': move_id, 
                       'journal_id': journal_id, 
                       'period_id': periodo_id, 
                       'name': 'S.S. Empresa', 
                       'debit': nom.ss_empresa, 
                       'ref': referencia   
                      }
            account_move_line_obj.create(cr, uid, ss_empresa)
            
            hacienda_publica = {
                        'account_id': cuentas['cuenta_hacienda_publica'], 
                        'move_id': move_id, 
                        'journal_id': journal_id, 
                        'period_id': periodo_id, 
                        'name': 'IRPF', 
                        'credit': retencion_irpf, 
                        'ref': referencia      
                        }
            account_move_line_obj.create(cr, uid, hacienda_publica)
            
            ss_acreedores = {
                        'account_id': cuentas['cuenta_ss_acreedores'], 
                        'move_id': move_id, 
                        'journal_id': journal_id,
                        'period_id': periodo_id, 
                        'name': 'S.S. Acreedores ', 
                        'credit': nom.ss_trabajador + nom.ss_empresa, 
                        'ref': referencia 
                        }
            account_move_line_obj.create(cr, uid, ss_acreedores)
            
            pendientes_pago = {
                        'account_id': cuentas['cuenta_pendientes_pago'], 
                        'move_id': move_id, 
                        'journal_id': journal_id, 
                        'period_id': periodo_id, 
                        'name': 'Sueldo Neto', 
                        'credit': sueldo_neto, 
                        'ref': referencia       
                        }
            account_move_line_obj.create(cr, uid, pendientes_pago)

            account_move_obj.write(cr, uid, [move_id], {'date': fechaNomina})
            account_move_obj.post(cr, uid, [move_id])
            self.write(cr, uid, ids, {'numero': numero})
            self.write(cr, uid, ids, {'state': 'confirmada', 'asiento_nomina_confirmada': move_id})
        return True

    def pagar_nomina(self, cr, uid, ids, *args):
        ##################################################################
        # OBJETOS
        ##################################################################
        account_journal_obj = self.pool.get('account.journal')
        account_period_obj = self.pool.get('account.period')
        account_move_obj = self.pool.get('account.move')
        account_move_line_obj = self.pool.get('account.move.line')
        ##################################################################
        cuentas = get_configuration(cr, uid, ids)
        for nom in self.browse(cr, uid, ids):
            if nom.state != 'confirmada':
                continue
            journal_id = cuentas['diario_destino']
            journal = account_journal_obj.browse(cr, uid, journal_id)
            fechaNomina = nom.fecha_nomina
            line = {}

            period_ids = account_period_obj.search(cr, uid, [('date_start', '<=', fechaNomina or time.strftime('%Y-%m-%d')), ('date_stop', '>=', fechaNomina or time.strftime('%Y-%m-%d'))])
            if len(period_ids):
                periodo_id = period_ids[0]

            referencia = nom.numero + ' : Pago ' + nom.employee_id.name + ' - ' + fechaNomina
            if nom.extra:
                referencia = "Pago de Paga Extra: " + nom.employee_id.name + ' - ' + fechaNomina
            move = {'ref': referencia, 'journal_id': journal_id, 'date': fechaNomina, 'period_id': periodo_id}

            move_id = account_move_obj.create(cr, uid, move)

            retencion_irpf = (nom.retribucion_bruta * nom.irpf) / 100
            sueldo_neto = nom.retribucion_bruta - retencion_irpf - nom.ss_trabajador
            anticipo = self.comprueba_anticipo(cr, uid, ids, fechaNomina, nom.employee_id.id)
            if anticipo and nom.extra == False:
                sueldo_neto -= anticipo
                
            cuenta_banco = {
                   'account_id': cuentas['cuenta_bancos'], 
                   'move_id': move_id, 
                   'journal_id': journal_id, 
                   'period_id': periodo_id, 
                   'name': 'Banco', 
                   'credit': sueldo_neto, 
                   'ref': referencia,
                   }
            account_move_line_obj.create(cr, uid, cuenta_banco)
            
            cuenta_pendiente = {
                              'account_id': cuentas['cuenta_pendientes_pago'], 
                              'move_id': move_id, 
                              'journal_id': journal_id, 
                              'period_id': periodo_id, 
                              'name': 'Renumeraciones pendientes', 
                              'debit': sueldo_neto, 
                              'ref': referencia,  
                            }
            account_move_line_obj.create(cr, uid, cuenta_pendiente)

            self.write(cr, uid, ids, {'state': 'pagada', 'asiento_nomina_pagada':move_id})
            account_move_obj.write(cr, uid, [move_id], {'date': fechaNomina})
            account_move_obj.post(cr, uid, [move_id])
        return True

    def cancelar_nomina(self, cr, uid, ids, *args):
        for nom in self.browse(cr, uid, ids):
            acc_obj = self.pool.get('account.move')
            if nom.state == 'confirmada':
                acc_obj.button_cancel(cr, uid, [nom.asiento_nomina_confirmada.id])
                self.write(cr, uid, ids, {'state': 'cancelada'})
        return True

hr_nomina()

class hr_anticipo(osv.osv):
    _name = 'hr.anticipo'
    _description = 'Anticipos de Nominas'
    _columns = {
            'name': fields.char('Anticipo', size=30),
            'employee_id': fields.many2one('hr.employee', 'Empleado', required=True, select="1", readonly=True),
            'fecha_anticipo': fields.date('Fecha de Anticipo', select="1", readonly=True),
            'cantidad': fields.float('Cantidad Anticipo', digits=(16, 2), readonly=True),
            'state': fields.selection((('borrador', 'Borrador'),
                                       ('confirmado', 'Confirmado'),
                                       ('pagado', 'Pagado'),
                                       ('cancelado', 'Cancelado')), 'Estado de anticipo', readonly=True, select="1"),
            'asiento_anticipo': fields.many2one('account.move', 'Asiento Anticipo', readonly=True),
    }

    _defaults = {
            'state': lambda * a:'borrador',
    }

    def confirmar_anticipo(self, cr, uid, ids, *args):
        ##################################################################
        # OBJETOS
        ##################################################################
        account_journal_obj = self.pool.get('account.journal')
        account_period_obj = self.pool.get('account.period')
        account_move_obj = self.pool.get('account.move')
        account_move_line_obj = self.pool.get('account.move.line')
        ##################################################################
        cuentas = get_configuration(cr, uid, ids)
        for anticipo in self.browse(cr, uid, ids):
            if anticipo.state != 'borrador':
                continue
            journal_id = cuentas['diario_destino']
            journal = account_journal_obj.browse(cr, uid, journal_id)
            fecha_anticipo = anticipo.fecha_anticipo
            #PERIODO
            period_ids = account_period_obj.search(cr, uid, [('date_start', '<=', fecha_anticipo or time.strftime('%Y-%m-%d')), ('date_stop', '>=', fecha_anticipo or time.strftime('%Y-%m-%d'))])
            if len(period_ids):
                periodo_id = period_ids[0]
            referencia = 'Anticipo: ' + anticipo.employee_id.name + ' - ' + fecha_anticipo
            
            move_val = {
                'ref': referencia, 
                'journal_id': journal_id, 
                'date': fecha_anticipo, 
                'period_id': periodo_id       
                    }
            move_id = account_move_obj.create(cr, uid, move_val)
            
            cuenta_anticipos_val = {
                    'account_id': cuentas['cuenta_anticipos'], 
                    'move_id': move_id, 
                    'journal_id': journal_id, 
                    'period_id': periodo_id, 
                    'name': 'Anticipo', 
                    'debit': anticipo.cantidad, 
                    'ref': referencia,
                                   }
            account_move_line_obj.create(cr, uid, cuenta_anticipos_val )
            
            cuenta_bancos_val = {
                      'account_id': cuentas['cuenta_bancos'], 
                      'move_id': move_id, 
                      'journal_id': journal_id, 
                      'period_id': periodo_id, 
                      'name': 'Bancos', 
                      'credit': anticipo.cantidad, 
                      'ref': referencia,         
                                 }
            account_move_line_obj.create(cr, uid, cuenta_bancos_val)
            self.write(cr, uid, ids, {'state': 'confirmado', 'asiento_anticipo': move_id})
            account_move_obj.write(cr, uid, [move_id], {'date': fecha_anticipo})
        return True

    def pagar_anticipo(self, cr, uid, ids, *args):
        for ant in self.browse(cr, uid, ids):
            if ant.state != 'confirmado':
                continue
            acc_obj = self.pool.get('account.move')
            acc_obj.post(cr, uid, [ant.asiento_anticipo.id])
            self.write(cr, uid, ids, {'state':'pagado'})
        return True

    def cancelar_anticipo(self, cr, uid, ids, *args):
        for ant in self.browse(cr, uid, ids):
            acc_obj = self.pool.get('account.move')
            if ant.state == 'confirmado':
                self.write(cr, uid, ids, {'state':'cancelado'})
        return True

hr_anticipo()