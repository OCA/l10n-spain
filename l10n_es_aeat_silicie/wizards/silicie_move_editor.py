# 2021 Obertix - Cubells <vicent@vcubells.net>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from ..models.product_product import PRODUCT_TYPES
from ..models.stock_move import TAX_POSITIONS


class SilicieMoveEditor(models.TransientModel):
    _name = "silicie.move.editor"
    _description = "Silicie Move Editor"

    factor_conversion_silicie = fields.Float(
        string="Factor Conversion SILICIE",
    )
    alcoholic_grade = fields.Float(
        string="Alcoholic Grade",
        digits=(5, 2),
    )
    silicie_product_type = fields.Selection(
        string="SILICIE Product Type",
        selection=PRODUCT_TYPES,
    )
    silice_tax_position = fields.Selection(
        string="SILICIE Tax Position",
        selection=TAX_POSITIONS,
    )
    silicie_move_type_id = fields.Many2one(
        string="Move Type SILICIE",
        comodel_name="aeat.move.type.silicie",
    )
    silicie_proof_type_id = fields.Many2one(
        string="Proof Type SILICIE",
        comodel_name="aeat.proof.type.silicie",
    )
    silicie_operation_num = fields.Char(
        string="SILICIE Operation Num.",
    )
    silicie_processing_id = fields.Many2one(
        string="Processing SILICIE",
        comodel_name="aeat.processing.silicie",
    )
    silicie_loss_id = fields.Many2one(
        string="Loss SILICIE",
        comodel_name="aeat.loss.silicie",
    )
    nc_code = fields.Char(
        string="NC Code",
    )
    product_key_silicie_id = fields.Many2one(
        string="Product Key SILICIE",
        comodel_name="aeat.product.key.silicie",
    )
    container_type_silicie_id = fields.Many2one(
        string="Container Type SILICIE",
        comodel_name="aeat.container.type.silicie",
    )
    epigraph_silicie_id = fields.Many2one(
        string="Epigraph SILICIE",
        comodel_name="aeat.epigraph.silicie",
    )
    uom_silicie_id = fields.Many2one(
        string="UoM SILICIE",
        comodel_name="aeat.uom.silicie",
    )
    notes_silice = fields.Char(
        string="Notes Silice",
    )
    density = fields.Float(
        string="Densidad SILICIE",
        digits=(3, 3),
    )

    @api.multi
    def _prepare_silicie_values(self):
        self.ensure_one()
        return {
            'silicie_move_type_id': self.silicie_move_type_id.id,
            'silicie_loss_id': self.silicie_loss_id.id,
            'silice_tax_position': self.silice_tax_position,
            'silicie_processing_id': self.silicie_processing_id.id,
            'silicie_operation_num': self.silicie_operation_num,
            'silicie_proof_type_id': self.silicie_proof_type_id.id,
            'epigraph_silicie_id': self.epigraph_silicie_id.id,
            'nc_code': self.nc_code,
            'product_key_silicie_id': self.product_key_silicie_id.id,
            'uom_silicie_id': self.uom_silicie_id.id,
            'alcoholic_grade': self.alcoholic_grade,
            'container_type_silicie_id': self.container_type_silicie_id.id,
            'factor_conversion_silicie': self.factor_conversion_silicie,
            'notes_silice': self.notes_silice,
            'density': self.density,
        }

    @api.multi
    def save_silicie_move(self):
        for move in self.env['stock.move'].browse(
                self.env.context.get('active_ids')):
            move.write(self._prepare_silicie_values())
