# -*- coding: utf-8 -*-
from osv import osv, fields


class wiz_baja(osv.osv_memory):
    _name = 'lopd.wizard.baja'
    _description = 'Wizard para solicitar baja'
    _columns = {
        'motivos': fields.char('Motivos de la supresión', size=140, required=True),
        'previsiones': fields.char('Destino de la información y previsiones adoptadas para su destrucción.', size=210, required=True),
    }

    def solicitud_baja(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids)[0]
        fichero = self.pool.get('lopd.fichero')
        active_ids = context.get('active_ids', [])
        values = {'type': 'ir.actions.act_window_close'}
        fichero.envio_baja(
            cr, uid, active_ids, context, this.motivos, this.previsiones)
        return values
wiz_baja()
