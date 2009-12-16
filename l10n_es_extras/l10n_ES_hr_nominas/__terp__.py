# -*- encoding: utf-8 -*-


{
    "name" : "Recursos Humanos: Gestión de Nóminas",
    "version" : "0.1",
    "author" : "Trazagest",
    "category" : "Generic Modules/Human Resources",
    "description": """ Recursos Humanos: Gestión de Nóminas
        Este módulo permite automatizar la creación de los asientos contables para las nóminas de los empleados.
        
        Uso del módulo:
            - El primer paso es configurar las cuentas y el diario en el que se van a contabilizar las nóminas para ello hay que ir a Administración -> Usuarios -> Arbol de la compañia -> Compañias y dentro de la página configuración de compañias configurar estas cuentas.
            - Se deben poner los datos de la nómina en la ficha del empleado en recursos humanos dentro de la pestaña salario
            - Para generar las nóminas se usa el wizard definido dentro de Recursos Humanos -> Nóminas -> Generar Nóminas
            - Para confirmar y pagar las nóminas se debe ir al menú Recursos Humanos -> Nóminas -> Ver Todas las Nóminas
            - Existen wizards para crear anticipos y pagas extras.
            - Para pagar los anticipos se debe ir al menú Recursos Humanos -> Nóminas -> Ver los anticipos

""",
    'author': 'Trazagest',
    'website': 'http://www.trazagest.com',
    'depends': ['base','hr','account'],
    'init_xml': [],
    'update_xml': ['security/ir.model.access.csv','view_nominas.xml','hr_nominas_wizard.xml','data/hr_nominas.xml'],
    'demo_xml': [],
    'installable': True,
    'active': False,    
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
