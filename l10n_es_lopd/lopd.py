# -*- coding: utf-8 -*-

from osv import fields, osv
import os
import time

# Extensión de res_country_state para evitar entradas duplicadas
class state_extension(osv.osv):
    _inherit = 'res.country.state'
    _name = 'res.country.state'
    #_columns = {'codigo':fields.char('Código númerico',size=2,help='Código numérico de la provincia definidos en la LOPD',readonly=True),}
    _sql_constraints = [
        #('cc_unico','unique (codigo, country_id)', 'No puede haber códigos repetidos en un pais'),
        ('nc_unico','unique (name, country_id)', 'La provincia ya existe en el pais'),
        ('cdc_unico','unique (code, country_id)', 'No puede haber códigos repetidos en un pais'),    
    ]

state_extension()

########################################################################################################
# Empresa
########################################################################################################

class lopd_actividades(osv.osv):
    _name = 'lopd.actividades'
    _description='Actividades de empresas'
    _columns= {
        'id':fields.integer('ID', required=True, readonly=True),
        'name':fields.char('Tipo', size=128, required=True),
        'codigo':fields.char('Código', size=3),
    }
    _sql_constraints = [('id_unico','unique (id)','¡El ID del tipo debe ser único!'),
                        ('nombre_unico','unique (name)','¡El nombre del tipo debe ser único!'),
                        ('codigo_unico','unique (codigo)','¡Los códigos de actividad no se pueden repetir!')]
    
lopd_actividades()

########################################################################################################
# Registro de locales
########################################################################################################

class lopd_locales(osv.osv):
    _name= 'lopd.locales'
    _description='Clase para registrar los locales de la empresa.'
    _columns = {
        'name':fields.char('Identificación', size=64, required=True),
        'domicilio': fields.char('Domicilio Social', size=100),
        'cp': fields.char('Código Postal', change_default=True, size=5),
        'localidad': fields.char('Localidad', size=50),
        'provincia': fields.many2one("res.country.state", 'Provincia', domain="[('country_id','=',pais)]"),
        'pais': fields.many2one('res.country', 'Pais'),    
        'tlf': fields.char('Teléfono', size=10),
        'fax': fields.char('Fax', size=10),
        'f_alta':fields.date('Fecha alta acceso', required = True),
        'f_baja':fields.date('Fecha baja acceso'),
        'descripcion':fields.text('Descripcción', size=250),
    }
    _defaults = {
        'pais': lambda *a: 67,
    }

lopd_locales()

########################################################################################################
# Registro de departamentos
########################################################################################################

class lopd_departamentos(osv.osv):
    _name= 'lopd.departamentos'
    _description='Clase para registrar los departamentos de la empresa.'
    _columns = {
        'id':fields.integer('ID', required=True, readonly=True),
        'name':fields.char('Nombre', size=64, required=True),
        'descripcion':fields.text('Descripcción', size=250),
        'locales':fields.many2one('lopd.locales','Local', required=True),

    }
    _defaults = {'locales':lambda self, cr, uid, context : context['locales'] if context and 'locales' in context else None }
    _sql_constraints = [('id_unico','unique (id)','¡El ID del recurso debe ser único!'),]

lopd_departamentos()

########################################################################################################
# Sistemas operativos
########################################################################################################

class lopd_sos_tipos(osv.osv):
    _name= 'lopd.sos.tipos'
    _description='Tipos de sistemas operativos'
    _columns = {
        'id':fields.integer('ID', required=True, readonly=True),
        'name':fields.char('Tipo', size=64, required=True),
    }
    _sql_constraints = [('id_unico','unique (id)','¡El ID del tipo debe ser único!'),
                        ('nombre_unico','unique (name)','¡El nombre del tipo debe ser único!')]
lopd_sos_tipos()

class lopd_sos(osv.osv):
    _name= 'lopd.sos'
    _description='Sistemas operativos'
    _columns = {
        'id':fields.integer('ID', required=True, readonly=True),
        'name':fields.many2one('lopd.sos.tipos','Nombre', required=True),
        'version':fields.char('Version', size=48, help="Especifique la versión del S.O. Ej: En caso de windows 'XP Profesional 2002', o en caso de Linux 'Debian 6 Squeeze'."),
        'fabricante':fields.char('Fabricante', size=48),
        'f_inst':fields.date('Fecha de instalación', required = True),
        # sca = Sistema de control de Accesos
        'sca':fields.selection([(1,'Sí'),(2,'No'),], 'SCA', help="Sistema de control de Accesos", required= True),
        # lif = Limitación de intentos fallidos
        'lif':fields.selection([(1,'Sí'),(2,'No'),], 'LIF', help="Limitación de intentos fallidos", required= True), 
    }
    _sql_constraints = [('id_unico','unique (id)','¡El ID del equipo debe ser único!'),    ]
    _defaults = {
        'sca': 2,
        'lif': 2,
        'f_inst': lambda *a: time.strftime('%Y-%m-%d'),
    }
    def action_dummy(self, cr, uid, ids, context={}): 
        return {}     
lopd_sos()

########################################################################################################
# Equipos (Ordenadores)
########################################################################################################

class lopd_equipos_tipos(osv.osv):
    _name= 'lopd.equipos.tipos'
    _description='Tipos de equipos'
    _columns = {
        'id':fields.integer('ID', required=True, readonly=True),
        'name':fields.char('Tipo', size=64, required=True),
    }
    _sql_constraints = [('id_unico','unique (id)','¡El ID del tipo debe ser único!'),
                        ('nombre_unico','unique (name)','¡El nombre del tipo debe ser único!')]
lopd_equipos_tipos()

class lopd_equipos(osv.osv):
    _name= 'lopd.equipos'
    _description='Clase para registrar los equipos de la empresa.'
    _columns = {
        'id':fields.integer('ID', required=True, readonly=True),
        'name':fields.char('Identificación', size=64, required=True),
        'descripcion':fields.text('Descripcción', size=250),
        'tipo':fields.many2one('lopd.equipos.tipos', 'Tipo', required=True),
        'f_alta':fields.date('Fecha alta', required = True),
        'f_baja':fields.date('Fecha baja'),
        # procedimiento de destrucción
        'p_destruccion':fields.selection([(1,'Sí'),(2,'No'),],'Proc. de destrucción'),
        #local al que pertenece
        'id_locales' : fields.many2one('lopd.locales','Locales'),
    }
    _sql_constraints = [('id_unico','unique (id)','¡El ID del equipo debe ser único!'),
                        ('name_unico','unique (name)','¡El nombre del equipo debe ser único!')]
    _defaults = {
        'id_locales': lambda self, cr, uid, context : context['id_locales'] if context and 'id_locales' in context else None , 
        'f_alta': lambda *a: time.strftime('%Y-%m-%d'),
        'p_destruccion': 2,
    }
lopd_equipos()

########################################################################################################
# Recursos
########################################################################################################

class lopd_recursos_tipos(osv.osv):
    _name= 'lopd.recursos.tipos'
    _description='Tipos de recursos'
    _columns = {
        'id':fields.integer('ID', required=True, readonly=True),
        'name':fields.char('Tipo', size=64, required=True),
    }
    _sql_constraints = [('id_unico','unique (id)','¡El ID del tipo debe ser único!'),
                        ('nombre_unico','unique (name)','¡El nombre del tipo debe ser único!')]
lopd_recursos_tipos()

class lopd_recursos(osv.osv):
    _name= 'lopd.recursos'
    _description='Clase para registrar los recursos de la empresa.'
    _columns = {
        'id':fields.integer('ID', required=True, readonly=True),
        'tipo':fields.many2one('lopd.recursos.tipos', 'Tipo', required=True),
        'name':fields.char('Identificación', size=64, required=True, help="Puede identificar el recurso por el nombre del modelo, pero recuerde, si dispone por ejemplo de 2 impresoras del mismo modelo, deberá identificarlas por nombres distintos, como por ejemplo Modelo XA-700_1 y XA-700_2."),
        'descripcion':fields.text('Descripcción', size=250),
        'f_alta':fields.date('Fecha alta', required = True),
        'f_baja':fields.date('Fecha baja'),
        'url':fields.char('URL*', help="En caso de tratarse de una página web indicar la URL", size=128),
        'corpnet' : fields.boolean('Red Corporativa', help="Marque esta casilla si el recurso pertenece a una red corporativa."),
        'intranet': fields.boolean('Intranet', help="Marque esta casilla si el recurso se encuentra en una intranet."),
        'internet': fields.boolean('Internet', help="Marque esta casilla si el recurso se encuentra en internet."),
        'lectura' : fields.boolean('Permiso de Lectura'),
        'escritura':fields.boolean('Permiso de Escritura'),
        #equipos relacionados
        'id_equipos' :fields.many2many('lopd.equipos','lopd_rel_eqre','id_re','id_eq','Equipos'),
    }
    _sql_constraints = [('id_unico','unique (id)','¡El ID del recurso debe ser único!'),
                        ('identificacion_unica','unique (name)','¡El nombre del recurso debe ser único!')]

    _defaults = {
        'f_alta': lambda *a: time.strftime('%Y-%m-%d'),
        'corpnet':lambda *a: False,
        'intranet':lambda *a: False,
        'internet':lambda *a: False,
    }
lopd_recursos()


########################################################################################################
# Programas
########################################################################################################

class lopd_programas_tipos(osv.osv):
    _name= 'lopd.programas.tipos'
    _description='Tipos de programas'
    _columns = {
        'id':fields.integer('ID', required=True, readonly=True),
        'name':fields.char('Tipo', size=64, required=True),
    }
    _sql_constraints = [('id_unico','unique (id)','¡El ID del tipo debe ser único!'),
                        ('nombre_unico','unique (name)','¡El nombre del tipo debe ser único!')]
lopd_programas_tipos()

class lopd_programas(osv.osv):
    _name= 'lopd.programas'
    _description='Clase para registrar los programas de la empresa.'
    _columns = {
        'id':fields.integer('ID', required=True, readonly=True),
        'tipo':fields.many2one('lopd.programas.tipos', 'Tipo de Programa', required=True),
        'name':fields.char('Nombre', size=64, required=True),
        'descripcion':fields.text('Descripción', size=250),
        'f_inst':fields.date('Fecha de instalación', required = True),
        'fabricante':fields.char('Fabricante', size=64),
        'version':fields.char('Versión', size=32),
        'p_licencia':fields.selection([(1,'Sí'),(2,'No'),],'¿Tiene licencia?', required=True),
        'licencia':fields.char('Licencia', size=64),
        # sca = Sistema de control de Accesos
        'sca':fields.selection([(1,'Sí'),(2,'No'),], 'SCA', help="Sistema de control de Accesos", required= True),
        # lif = Limitación de intentos fallidos
        'lif':fields.selection([(1,'Sí'),(2,'No'),], 'LIF', help="Limitación de intentos fallidos",required= True),        
        # Sistemas Operativos en el que funciona el programa
        'id_sos': fields.many2many('lopd.sos' ,'lopd_rel_prso', 'pr_id', 'so_id','Seleccionar los SO en que funciona'),
        #equipos relacionados
        'id_equipos':fields.many2many('lopd.equipos','lopd_rel_eqpr','id_pr','id_eq','Equipos'),
    }
    _sql_constraints = [('id_unico','unique (id)','¡El ID del recurso debe ser único!'),]
    _defaults = {        
        'f_inst': lambda *a: time.strftime('%Y-%m-%d'),
        'p_licencia': 2,
        'sca': 2,
        'lif': 2,
    }
lopd_programas()

########################################################################################################
# Registro de Zonas de Acceso Restringido
########################################################################################################


class lopd_zar(osv.osv):
    _name= 'lopd.zar'
    _description='Clase para registrar las ZAR de la empresa.'
    _columns = {
        'id':fields.integer('ID', required=True, readonly=True),
        'name':fields.char('Nombre', size=64, required=True),
        'descripcion':fields.text('Descripcción', size=250),
        'locales':fields.many2one('lopd.locales','Locales'),
        'departamento':fields.many2one('lopd.departamentos','Departamento', required=True),
    }
    _defaults = {
        'locales': lambda self, cr, uid, context : context['locales'] if context and 'locales' in context else None,
        'departamento': lambda self, cr, uid, context : context['departamento'] if context and 'departamento' in context else None ,
    }
    _sql_constraints = [('id_unico','unique (id)','¡El ID del recurso debe ser único!'),]
        
    def onchange_locales(self, cr, uid, ids, locales):
        v = {'departamento':0}
        return {'value': v}

lopd_zar()

########################################################################################################
# Soportes
########################################################################################################

class lopd_soportes_tipos(osv.osv):
    _name = 'lopd.soportes.tipos'
    _description='Tipos de soportes'
    _columns= {
        'id':fields.integer('ID', required=True, readonly=True),
        'name':fields.char('Tipo', size=64, required=True),
    }
    _sql_constraints = [('id_unico','unique (id)','¡El ID del tipo debe ser único!'),
                        ('nombre_unico','unique (name)','¡El nombre del tipo debe ser único!')]
lopd_soportes_tipos()

class lopd_soportes(osv.osv):
    _name= 'lopd.soportes'
    _description='Clase para registrar los soportes de la empresa.'
    _columns = {
        'id':fields.integer('ID', required=True, readonly=True),
        'tipo':fields.many2one('lopd.soportes.tipos', 'Tipo de soporte', required=True),
        'name':fields.char('Identificación', size=64, required=True),
        'descripcion':fields.text('Descripcción', size=250),
        'tipo_info':fields.text('Tipo de información', size=250),
        'f_alta':fields.date('Fecha alta', required = True),
        'f_baja':fields.date('Fecha baja'),
        # reutil = Reutilización del soporte
        'reutil':fields.selection([(1,'Sí'),(2,'No'),], 'Reutilización', required= True),
        # en_zar = Esta en una zona de control de acceso (zar)
        'en_zar':fields.selection([(1,'Sí'),(2,'No'),], '¿Está en una Zar?', required= True, help="¿Se encuentra el soporte en una zona de acceso restringida?"),
        'zar':fields.many2one('lopd.zar', 'ZAR'),
        'locales':fields.many2one('lopd.locales','Locales'),
        'departamentos':fields.many2one('lopd.departamentos','Departamentos'),
        # mdd = Método de destrucción 
        'mdd':fields.selection([(1,'Sí'),(2,'No'),], 'Método de destrucción', required= True),
    }
    _sql_constraints = [('id_unico','unique (id)','¡El ID del recurso debe ser único!'),]
    _defaults = {
        'f_alta':lambda *a: time.strftime('%Y-%m-%d'),
        'reutil': 2,
        'en_zar': 2,
        'mdd': 2,
    }
    def onchange_locales(self, cr, uid, ids, locales):
        v = {'departamentos':0, 'en_zar':2, 'zar':0}
        return {'value':v}

    def onchange_departamentos(self, cr, uid, ids, departamentos):
        v = {'en_zar':2, 'zar':0}
        return {'value': v}

    def onchange_en_zar(self, cr, uid, ids, departamentos):
        v = {'zar':0}
        return {'value': v}

lopd_soportes()

########################################################################################################
# Extensiones para las relaciones
########################################################################################################

class lopd_sos_ext(osv.osv):
    _name='lopd.sos'
    _inherit='lopd.sos'
    _columns = {'id_programas': fields.many2many('lopd.programas' ,'lopd_rel_prso', 'so_id', 'pr_id','Programas asociados'),}
lopd_sos_ext()

class lopd_equipos_ext(osv.osv):
    _name='lopd.equipos'
    _inherit='lopd.equipos'
    _columns = {
        #programas relacionados
        'id_programas':fields.many2many('lopd.programas','lopd_rel_eqpr','id_eq','id_pr','Programas'),
        #recursos relacionados
        'id_recursos' :fields.many2many('lopd.recursos','lopd_rel_eqre','id_eq','id_re','Recursos'),
    }
lopd_equipos_ext()

class lopd_locales_ext(osv.osv):
    _name='lopd.locales'
    _inherit='lopd.locales'
    _columns = {
        'id_equipos' : fields.one2many('lopd.equipos','id_locales','Equipos'),
        'id_departamentos': fields.one2many('lopd.departamentos', 'locales', 'Departamentos'),            
    }
lopd_locales_ext()

class lopd_departamentos_ext(osv.osv):
    _name='lopd.departamentos'
    _inherit='lopd.departamentos'
    _columns = { 'id_zars': fields.one2many('lopd.zar','departamento','Zar relacionadas')}
lopd_departamentos_ext()

class lopd_zar_ext(osv.osv):
    _name='lopd.zar'
    _inherit='lopd.zar'
    _columns = { 'id_soporte':fields.one2many('lopd.soportes','zar','Soportes')}
lopd_zar_ext()

########################################################################################################
# Relación usuario/equipo/recurso/programa
########################################################################################################

#class lopd_relations(osv.osv_memory):
#    _name='lopd.relations'
#    _columns = {
#        'id_usuario':fields.many2many('res.users','usuario_rel','id_rel','id_usr','Usuarios'),
#        'id_equipo':fields.many2many('lopd.equipos','equipo_rel','id_usr','id_eq', 'Equipos'),
#        'id_recurso':fields.many2many('lopd.recursos','recurso_rel','id_usr','id_re', 'Recursos'),
#        'id_programa':fields.many2many('lopd.programas','programa_rel','id_usr','id_pr', 'Programas'),
#    }
#lopd_relations

###############################################################################################################################
###############################################################################################################################
###############################################################################################################################
#'country_id': fields.related('state_id', 'country_id', type="many2one", relation="res.country", string="Country", store=False)

    #def test_f(self, cr, uid, ids, context={}):
    #    name = os.getuid()
    #    filename = "/tmp/test.txt"        
    #    file = open(filename, 'w')
    #    file.write(str(name))
    #    #file.write("Este es un fichero generado por una funcion :-)")
    #    file.close()
    #    return 1

    #def anexarFicheiro(self,cr,uid,ids,conteudo,context={}):
    #    import base64
    #    nome='SDD_'+time.strftime('%Y%m%d_%H%M%S')
    #    attach_id=self.pool.get('ir.attachment').create(cr, uid, {
    #        'name': nome,'datas': base64.encodestring(conteudo),
    #        'datas_fname': nome, 'res_model': 'res.company', 
    #        'res_id': ids,}, context=context)
    #    return True
    #self.anexarFicheiro(cr,uid,empresa_id,conteudo)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
