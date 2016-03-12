# -*- coding: utf-8 -*-
# © 2015 Omar Castiñeira (Comunitea)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class ResPartner(models.Model):
    _inherit = "res.partner"

    facturae = fields.Boolean('Factura electrónica')
    organo_gestor = fields.Char('Órgano gestor', size=10)
    unidad_tramitadora = fields.Char('Unidad tramitadora', size=10)
    oficina_contable = fields.Char('Oficina contable', size=10)
    organo_proponente = fields.Char('Órgano proponente', size=10)
