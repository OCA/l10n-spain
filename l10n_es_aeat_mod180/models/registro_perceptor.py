# -*- encoding: utf-8 -*-

from odoo import _, api, fields, models


class RegistroPerceptor(models.Model):
    _name = 'registro.perceptor'
    _description = 'Registro de perceptor'

    report_id = fields.Many2one('l10n.es.aeat.mod180.report', string='AEAT 180 Report', ondelete="cascade")
    partner_id = fields.Many2one('res.partner', string='Empresa')
    informacion_catastral_id = fields.Many2one('informacion.catastral', string='Información catastral')
    signo = fields.Selection(selection=[(' ', "Positivo"), ('N', "Negativo")], string='Signo Base Retenciones',)
    base_retenciones = fields.Float(string='Base retenciones e ingresos a cuenta', digits=(13, 2))
    cuota_retenciones = fields.Float(string='Retenciones e ingresos a cuenta', digits=(13, 2))
    porcentaje_retencion = fields.Float(string='% Retención', digits=(2, 2))
    ejercicio_devengo = fields.Integer(string='Ejercicio Devengo')
    base_move_line_ids = fields.Many2many('account.move.line', 'reg_perceptor_base_move_line_rel', 'reg_perceptor_id', 'move_line_id', string='Apuntes contable de base')
    cuota_move_line_ids = fields.Many2many('account.move.line', 'reg_perceptor_cuota_move_line_rel', 'reg_perceptor_id','move_line_id', string='Apuntes contable de cuota')

    def action_get_base_move_lines(self):
        res = self.env.ref('account.action_account_moves_all_a').read()[0]
        view = self.env.ref('l10n_es_aeat_mod180.account_move_line_mod180_view_tree')
        res['views'] = [(view.id, 'tree')]
        res['domain'] = [('id', 'in', self.base_move_line_ids.ids)]
        return res

    def action_get_cuota_move_lines(self):
        res = self.env.ref('account.action_account_moves_all_a').read()[0]
        view = self.env.ref('l10n_es_aeat_mod180.account_move_line_mod180_view_tree')
        res['views'] = [(view.id, 'tree')]
        res['domain'] = [('id', 'in', self.cuota_move_line_ids.ids)]
        return res

