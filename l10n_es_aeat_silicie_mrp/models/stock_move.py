# Copyright 2020 Javier de las Heras <jheras@alquemy.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    extract = fields.Float(
        string="Extracto SILICIE",
    )

    def _action_done(self):
        move = super(StockMove, self)._action_done()
        move.generate_silicie_fields()
        return move

    @api.multi
    def generate_silicie_fields(self):
        super().generate_silicie_fields()
        for move in self:
            if move.send_silicie:
                continue
            is_silicie_move = False
            if move.product_id.product_tmpl_id.silicie_product_type == "none":
                continue
            # Production
            production = move.production_id or move.raw_material_production_id
            if move.location_id.usage == "production" and \
                    move.location_dest_id.usage == "internal":
                is_silicie_move = True
                move.silicie_proof_type_id = self.env.ref(
                    "l10n_es_aeat_silicie.aeat_proof_type_silicie_j09")
                move.silicie_move_type_id = self.env.ref(
                    "l10n_es_aeat_silicie.aeat_move_type_silicie_a15")
                if not move.silicie_operation_num:
                    move.silicie_operation_num = self.env[
                        "ir.sequence"].next_by_code("silicie.operation")
                move.silice_tax_position = "1"
                move.silicie_processing_id = \
                    production.silicie_processing_id or \
                    production.routing_id.silicie_processing_id
            # Production BoM
            elif move.location_id.usage == "internal" and \
                    move.location_dest_id.usage == "production":
                is_silicie_move = True
                move.silicie_proof_type_id = self.env.ref(
                    "l10n_es_aeat_silicie.aeat_proof_type_silicie_j09")
                move.silicie_move_type_id = self.env.ref(
                    "l10n_es_aeat_silicie.aeat_move_type_silicie_a14")
                if not move.silicie_operation_num:
                    move.silicie_operation_num = self.env[
                        "ir.sequence"].next_by_code("silicie.operation")
                loss_type = production.silicie_loss_id
                if loss_type:
                    move.silicie_loss_id = loss_type.id
                move.silice_tax_position = "1"
                move.silicie_processing_id = \
                    production.silicie_processing_id or \
                    production.routing_id.silicie_processing_id
            # Loss
            elif move.location_id.usage == "internal" and \
                    move.location_dest_id.usage == "inventory" and \
                    move.location_dest_id.scrap_location:
                is_silicie_move = True
                move.silicie_proof_type_id = self.env.ref(
                    "l10n_es_aeat_silicie.aeat_proof_type_silicie_j11")
                move.silice_tax_position = "1"
                if move.scrap_ids:
                    move.notes_silice = move.scrap_ids[:1].origin
                loss_type = move.scrap_ids[:1].silicie_loss_id
                move_type = move.scrap_ids[:1].silicie_move_type_id
                if loss_type and move_type:
                    move.silicie_move_type_id = move_type.id
                    move.silicie_loss_id = loss_type.id
                else:
                    move.silicie_move_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a28")
            if is_silicie_move:
                move.silicie_product_type = \
                    move.product_id.product_tmpl_id.silicie_product_type
                move.factor_conversion_silicie = \
                    move.product_id.product_tmpl_id.factor_conversion_silicie
                move.alcoholic_grade = \
                    move.product_id.product_tmpl_id.alcoholic_grade
                move.nc_code = move.product_id.product_tmpl_id.nc_code
                move.product_key_silicie_id = \
                    move.product_id.product_tmpl_id.product_key_silicie_id
                move.container_type_silicie_id = \
                    move.product_id.product_tmpl_id.container_type_silicie_id
                move.epigraph_silicie_id = \
                    move.product_id.product_tmpl_id.epigraph_silicie_id
                move.uom_silicie_id = \
                    move.product_id.product_tmpl_id.uom_silicie_id
                move.fiscal_position_id = \
                    move.picking_id.partner_id.property_account_position_id
                # Check if all fields have been correctly generated
                move.check_silicie_fields()

    @api.multi
    def _get_data_mrp_dict(self, lot_moves):
        self.ensure_one()
        Lots = self.env["stock.production.lot"]
        a14_type = self.env.ref(
            "l10n_es_aeat_silicie.aeat_move_type_silicie_a14")
        a02_type = self.env.ref(
            "l10n_es_aeat_silicie.aeat_move_type_silicie_a02")
        a08_type = self.env.ref(
            "l10n_es_aeat_silicie.aeat_move_type_silicie_a08")
        data = {}
        if self.product_id.silicie_product_type == "beer":
            qty_done = 0.0
            extract = 0.0
            sum_extract = 0.0
            density = 1.0
            sum_density = 0.0
            kg_extract = 0.0
            for lot_move in lot_moves:
                qty_done += lot_move["qty_done"]
                lot_id = Lots.browse(lot_move["lot_id"])
                density += lot_id.density
                sum_density += lot_id.density * lot_move["qty_done"]
                if self.product_id.product_class == "raw":
                    extract += lot_id.extract
                    sum_extract += lot_id.extract * lot_move["qty_done"]
            if extract:
                extract = sum_extract / qty_done
                if self.silicie_move_type_id in (a14_type, a02_type):
                    kg_extract = extract * qty_done / 100
            if density:
                density = sum_density / qty_done
                if density:
                    data["grado_plato"] = (density - 1000) / 4
                else:
                    data["grado_plato"] = 0
            if not extract:
                extract = ""
            if not kg_extract:
                kg_extract = ""
            if not density:
                density = ""
            data['qty_done'] = qty_done
            data['extract'] = extract
            data['kg_extract'] = kg_extract
            data['density'] = density
            if self.product_id.product_class == "final":
                data["extract"] = ""
                data["kg_extract"] = ""
        return data

    @api.multi
    def _prepare_values(self):
        self.ensure_one()
        lot_moves = []
        for group in self.env['stock.move.line'].read_group([
                ('move_id', 'in', self.ids)],
                ['lot_id', 'qty_done'],
                ['lot_id']):
            if group['lot_id']:
                lot_moves.append({
                    'lot_id': group['lot_id'][0],
                    'qty_done': group['qty_done'],
                })
        data = self._get_data_mrp_dict(lot_moves)
        values = super()._prepare_values()
        values.update({
            "Porcentaje de Extracto": data.get("extract", ""),
            "Kg. - Extracto": data.get("kg_extract", ""),
            "Grado Alcohólico": data.get("alcoholic_grade", ""),
            "Densidad": data.get("density", ""),
            "Grado Plato Medio": data.get("grado_plato", ""),
        })
        return values

    @api.multi
    def _get_move_fields(self):
        self.ensure_one()
        values = super()._get_move_fields()
        values.update({
            'extract': self.extract,
        })
        return values
