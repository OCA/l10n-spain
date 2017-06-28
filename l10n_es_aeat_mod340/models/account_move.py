# -*- coding: utf-8 -*-
# Copyright 2017 - Aselcis Consulting (http://www.aselcis.com)
#                - Miguel Paraíso <miguel.paraiso@aselcis.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, fields, _


OPERATION_KEYS = [
    (' ', 'Operaciones habituales'),
    ('A', 'A - Asiento resumen de facturas'),
    ('B', 'B - Asiento resumen de tique'),
    ('C', 'C - Factura con varios asientos (varios tipos impositivos)'),
    ('D', 'D - Factura rectificativa'),
    ('E', 'E - IVA/IGIC devengado pendiente de emitir factura'),
    ('F', 'F - Adquisiciones realizadas por las agencias de viajes directamente en interés del viajero'),
    ('G', 'G - Régimen especial de grupo de entidades en IVA o IGIC'),
    ('H', 'H - Régimen especial de oro de inversión'),
    ('I', 'I - Inversión del Sujeto pasivo (ISP)'),
    ('J', 'J - Tiques'),
    ('K', 'K - Rectificación de errores registrales'),
    ('L', 'L - Adquisiciones a comerciantes minoristas del IGIC'),
    ('M', 'M - IVA/IGIC facturado pendiente de devengar'),
    ('N', 'N - Facturación de las prestaciones de servicios de agencias de viaje que actúan como mediadoras en nombre '
          'y por cuenta ajena'),
    ('O', 'O - Factura emitida en sustitución de tiques facturados y declarados'),
    ('P', 'P - Adquisiciones intracomunitarias de bienes'),
    ('Q', 'Q - Operaciones a las que se aplique el Régimen especial de bienes usados, objetos de arte, antigüedades y '
          'objetos de colección'),
    ('R', 'R - Operación de arrendamiento de local de negocio'),
    ('S', 'S - Subvenciones, auxilios o ayudas satisfechas o recibidas, tanto por parte de Administraciones públicas '
          'como de entidades privadas'),
    ('T', 'T - Cobros por cuenta de terceros'),
    ('U', 'U - Operación de seguros'),
    ('W', 'W - Operaciones sujetas al Impuesto sobre la Producción, los Servicios y la Importación en las Ciudades de '
          'Ceuta y Melilla'),
    ('X', 'X - Operaciones por las que los empresarios o profesionales que satisfagan compensaciones agrícolas, '
          'ganaderas y/o pesqueras hayan expedido el recibo correspondiente'),
    ('Z', 'Z - Régimen especial del criterio de caja'),
]


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def _get_operation_key_by_tax(self, tax_description):
        if not tax_description:
            return False
        else:
            if tax_description in ['P_IVA21_IC_BC_1', 'P_IVA21_IC_BC_2', 'P_IVA4_IC_BC_1', 'P_IVA4_IC_BC_2',
                                   'P_IVA10_IC_BC_1', 'P_IVA10_IC_BC_2']:
                return 'P'
            elif tax_description in ['P_IVA21_SP_IN_1', 'P_IVA21_SP_IN_2', 'P_IVA4_SP_IN_1', 'P_IVA4_SP_IN_2',
                                     'P_IVA10_SP_IN_1', 'P_IVA10_SP_IN_2']:
                return 'I'
            else:
                return False

    @api.one
    @api.depends('line_ids')
    def _compute_mod340_operation_key(self):
        operation_key = False
        for line in self.line_ids:
            for tax_id in line.tax_ids:
                if tax_id.mod340:
                    operation_key = self._get_operation_key_by_tax(tax_id.description)
                    if operation_key:
                        self.mod340_operation_key = operation_key
                        return
        if not operation_key:
            self.mod340_operation_key = ' '

    mod340_operation_key = fields.Selection(selection=OPERATION_KEYS, compute='_compute_mod340_operation_key',
                                            string='Operation key', store=True)
