# Copyright 2020 Javier de las Heras <jheras@alquemy.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, exceptions, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    factor_conversion_silicie = fields.Float(
        string='Factor Conversion SILICIE',
    )

    qty_conversion_silicie = fields.Float(
        string='Qty Conversion SILICIE',
        compute='_compute_qty_conversion_silicie',
        store=True,
        digits=(16, 3),)

    alcoholic_grade = fields.Float(
        string='Alcoholic Grade',
        digits=(5, 2),
    )

    absolute_alcohol = fields.Float(
        string='Absolute Alcohol',
        compute='_compute_absolute_alcohol',
        store=True,
        digits=(16, 3),)

    silicie_product_type = fields.Selection(
        string='SILICIE Product Type',
        selection=[('none', 'None'),
                   ('alcohol', 'Alcohol'),
                   ('beer', 'Beer'),
                   ('intermediate', 'Intermediate'),
                   ('intermedieate_art', 'Intermediate Art. 32 LIE'),
                   ('wine', 'Wine'),
                   ('vinegar', 'Vinegar'),
                   ('hydrocarbons', 'Hydrocarbons'),
                   ('tobacco', 'Tobacco')],
        default='none',
        required=True,
    )

    silice_tax_position = fields.Selection(
        string='SILICIE Tax Position',
        selection=[('1', 'NO SUJETO'),
                   ('2', 'SUSPENSIVO'),
                   ('3', 'EXENTO'),
                   ('4', 'IMPUESTO DEVENGADO TIPO PLENO'),
                   ('5', 'IMPUESTO DEVENGADO TIPO REDUCIDO'),
                   ('6', 'IMPUESTO DEVENGADO A TIPO DE CANARIAS'), ]
    )

    silicie_move_type_id = fields.Many2one(
        string='Move Type SILICIE',
        comodel_name='aeat.move.type.silicie',
        ondelete='restrict',
    )

    silicie_proof_type_id = fields.Many2one(
        string='Proof Type SILICIE',
        comodel_name='aeat.proof.type.silicie',
        ondelete='restrict',
    )

    silicie_operation_num = fields.Char(
        string='SILICIE Operation Num.',
    )

    silicie_processing_id = fields.Many2one(
        string='Processing SILICIE',
        comodel_name='aeat.processing.silicie',
        ondelete='restrict',
    )

    silicie_loss_id = fields.Many2one(
        string='Loss SILICIE',
        comodel_name='aeat.loss.silicie',
        ondelete='restrict',
    )

    nc_code = fields.Char(
        string='NC Code',
    )

    silicie_move_number = fields.Char(
        string='SILICIE Move Number',
        copy=False,
    )

    silicie_entry_type = fields.Selection(
        string='SILICIE Entry Type',
        selection=[('1', 'Alta de Asiento'), ('2', 'Anulación de Asiento')]
    )

    product_key_silicie_id = fields.Many2one(
        string='Product Key SILICIE',
        comodel_name='aeat.product.key.silicie',
        ondelete='restrict',
    )

    container_type_silicie_id = fields.Many2one(
        string='Container Type SILICIE',
        comodel_name='aeat.container.type.silicie',
        ondelete='restrict',
    )

    epigraph_silicie_id = fields.Many2one(
        string='Epigraph SILICIE',
        comodel_name='aeat.epigraph.silicie',
        ondelete='restrict',
    )

    uom_silicie_id = fields.Many2one(
        string='UoM SILICIE',
        comodel_name='aeat.uom.silicie',
        ondelete='restrict',
    )

    send_silicie = fields.Boolean(
        string='Send SILICIE',
        readonly=True,
        store=True,
        compute='_compute_send_silicie',)

    not_declare = fields.Boolean(
        string='Not Declare',
        copy=False,
    )

    date_send_silicie = fields.Datetime(
        string='Date Send SILICIE',
        readonly=True,
        copy=False,
    )

    fiscal_position_id = fields.Many2one(
        string='Fiscal Position',
        comodel_name='account.fiscal.position',
        ondelete='restrict',
    )

    notes_silice = fields.Char(
        string='Notes Silice',
        copy=False,
    )

    fields_check = fields.Boolean(
        string='Check Fields',
        copy=False,)

    @api.depends('date_send_silicie')
    def _compute_send_silicie(self):
        for record in self:
            if record.date_send_silicie:
                record.send_silicie = True
            else:
                record.send_silicie = False

    @api.depends('factor_conversion_silicie', 'product_uom_qty')
    def _compute_qty_conversion_silicie(self):
        for record in self:
            record.qty_conversion_silicie = record.product_uom_qty * \
                record.factor_conversion_silicie

    @api.depends('qty_conversion_silicie', 'alcoholic_grade')
    def _compute_absolute_alcohol(self):
        for record in self:
            record.absolute_alcohol = (
                record.alcoholic_grade * record.qty_conversion_silicie) / 100

    @api.multi
    def generate_silicie_fields(self):
        for move in self:
            if move.send_silicie or move.not_declare:
                continue
            is_silicie_move = False
            if move.product_id.product_tmpl_id.silicie_product_type != 'none':
                if move.product_id.product_tmpl_id.silicie_product_type == 'alcohol':
                    # Sale
                    if move.location_id.usage == 'internal' and move.location_dest_id.usage == 'customer':
                        is_silicie_move = True
                        move.silicie_proof_type_id = self.env.ref(
                            'l10n_es_aeat_silicie.aeat_proof_type_silicie_j05')
                        if move.fiscal_position_id.silicie_partner_identification_type == 'national':
                            move.silicie_move_type_id = self.env.ref(
                                'l10n_es_aeat_silicie.aeat_move_type_silicie_a08')
                            move.silice_tax_position = '4'
                        elif move.fiscal_position_id.silicie_partner_identification_type == 'canarias':
                            move.silicie_move_type_id = self.env.ref(
                                'l10n_es_aeat_silicie.aeat_move_type_silicie_a09')
                            move.silice_tax_position = '6'
                        elif move.fiscal_position_id.silicie_partner_identification_type == 'intra':
                            move.silicie_move_type_id = self.env.ref(
                                'l10n_es_aeat_silicie.aeat_move_type_silicie_a10')
                        elif move.fiscal_position_id.silicie_partner_identification_type == 'export':
                            move.silicie_move_type_id = self.env.ref(
                                'l10n_es_aeat_silicie.aeat_move_type_silicie_a11')
                    # Sale Refund
                    elif move.location_id.usage == 'customer' and move.location_dest_id.usage == 'internal':
                        is_silicie_move = True
                        move.silicie_proof_type_id = self.env.ref(
                            'l10n_es_aeat_silicie.aeat_proof_type_silicie_j05')
                        if move.fiscal_position_id.silicie_partner_identification_type == 'national':
                            move.silicie_move_type_id = self.env.ref(
                                'l10n_es_aeat_silicie.aeat_move_type_silicie_a02')
                            move.silice_tax_position = '4'
                        elif move.fiscal_position_id.silicie_partner_identification_type == 'canarias':
                            move.silicie_move_type_id = self.env.ref(
                                'l10n_es_aeat_silicie.aeat_move_type_silicie_a03')
                            move.silice_tax_position = '6'
                        elif move.fiscal_position_id.silicie_partner_identification_type == 'intra':
                            move.silicie_move_type_id = self.env.ref(
                                'l10n_es_aeat_silicie.aeat_move_type_silicie_a04')
                        elif move.fiscal_position_id.silicie_partner_identification_type == 'export':
                            move.silicie_move_type_id = self.env.ref(
                                'l10n_es_aeat_silicie.aeat_move_type_silicie_a06')
                    # Purchase
                    elif move.location_id.usage == 'supplier' and move.location_dest_id.usage == 'internal':
                        is_silicie_move = True
                        move.silicie_proof_type_id = self.env.ref(
                            'l10n_es_aeat_silicie.aeat_proof_type_silicie_j01')
                        move.reference = move.purchase_line_id.order_id.arc or move.reference
                        if move.fiscal_position_id.silicie_partner_identification_type == 'national':
                            move.silicie_move_type_id = self.env.ref(
                                'l10n_es_aeat_silicie.aeat_move_type_silicie_a02')
                            move.silice_tax_position = '1'
                        elif move.fiscal_position_id.silicie_partner_identification_type == 'canarias':
                            move.silicie_move_type_id = self.env.ref(
                                'l10n_es_aeat_silicie.aeat_move_type_silicie_a03')
                        elif move.fiscal_position_id.silicie_partner_identification_type == 'intra':
                            move.silicie_move_type_id = self.env.ref(
                                'l10n_es_aeat_silicie.aeat_move_type_silicie_a04')
                        elif move.fiscal_position_id.silicie_partner_identification_type == 'export':
                            move.silicie_move_type_id = self.env.ref(
                                'l10n_es_aeat_silicie.aeat_move_type_silicie_a06')
                    # Purchase Refund
                    elif move.location_id.usage == 'internal' and move.location_dest_id.usage == 'supplier':
                        is_silicie_move = True
                        move.silicie_proof_type_id = self.env.ref(
                            'l10n_es_aeat_silicie.aeat_proof_type_silicie_j05')
                        if move.fiscal_position_id.silicie_partner_identification_type == 'national':
                            move.silicie_move_type_id = self.env.ref(
                                'l10n_es_aeat_silicie.aeat_move_type_silicie_a08')
                            move.silice_tax_position = '1'
                        elif move.fiscal_position_id.silicie_partner_identification_type == 'canarias':
                            move.silicie_move_type_id = self.env.ref(
                                'l10n_es_aeat_silicie.aeat_move_type_silicie_a09')
                        elif move.fiscal_position_id.silicie_partner_identification_type == 'intra':
                            move.silicie_move_type_id = self.env.ref(
                                'l10n_es_aeat_silicie.aeat_move_type_silicie_a10')
                        elif move.fiscal_position_id.silicie_partner_identification_type == 'export':
                            move.silicie_move_type_id = self.env.ref(
                                'l10n_es_aeat_silicie.aeat_move_type_silicie_a11')

                    '''
                    # Internal
                    elif move.location_id.usage == 'internal' and move.location_dest_id.usage == 'internal':
                        move.clear_silicie_fields()
                    # Inventory Adjustment
                    elif move.location_id.usage == 'inventory' or move.location_dest_id.usage == 'inventory':
                        move.clear_silicie_fields()
                    '''

                    if is_silicie_move:
                        move.silicie_product_type = move.product_id.product_tmpl_id.silicie_product_type
                        move.factor_conversion_silicie = move.product_id.product_tmpl_id.factor_conversion_silicie
                        move.alcoholic_grade = move.product_id.product_tmpl_id.alcoholic_grade
                        move.nc_code = move.product_id.product_tmpl_id.nc_code
                        move.product_key_silicie_id = move.product_id.product_tmpl_id.product_key_silicie_id
                        move.container_type_silicie_id = move.product_id.product_tmpl_id.container_type_silicie_id
                        move.epigraph_silicie_id = move.product_id.product_tmpl_id.epigraph_silicie_id
                        move.uom_silicie_id = move.product_id.product_tmpl_id.uom_silicie_id
                        move.fiscal_position_id = move.picking_id.partner_id.property_account_position_id
                        # Check if all fields have been correctly generated
                        move.check_silicie_fields()
            '''
            else:
                move.clear_silicie_fields()
            '''

    @api.multi
    def clear_silicie_fields(self):
        for move in self:
            move.silicie_product_type = 'none'
            move.factor_conversion_silicie = 0
            move.alcoholic_grade = 0
            move.nc_code = ''
            move.product_key_silicie_id = False
            move.container_type_silicie_id = False
            move.epigraph_silicie_id = False
            move.uom_silicie_id = False
            move.fiscal_position_id = False
            move.silicie_proof_type_id = False
            move.silicie_move_type_id = False
            move.silicie_processing_id = False
            move.silicie_loss_id = False
            move.notes_silice = ''

    def _action_done(self):
        move = super(StockMove, self)._action_done()
        move.generate_silicie_fields()
        return move

    @api.model
    def cron_generate_silicie_fields(self):
        moves = self.env['stock.move'].search(
            [("state", "=", 'done'),
             ('silicie_product_type', '!=', 'none'),
             ('date_send_silicie', '=', False)])
        moves.generate_silicie_fields()
        moves = self.env['stock.move'].search(
            [("state", "=", 'done'),
             ('silicie_product_type', '!=', 'none')])
        moves.check_silicie_fields()
        return

    @api.multi
    def check_silicie_fields(self):
        a14_type = self.env.ref(
            'l10n_es_aeat_silicie.aeat_move_type_silicie_a14')
        a15_type = self.env.ref(
            'l10n_es_aeat_silicie.aeat_move_type_silicie_a15')
        a32_type = self.env.ref(
            'l10n_es_aeat_silicie.aeat_move_type_silicie_a32')
        silicie_domain = ('state', '=', 'done')
        for record in self:
            if record.silice_tax_position and record.silicie_proof_type_id and record.epigraph_silicie_id \
                    and record.product_key_silicie_id and record.container_type_silicie_id and \
                record.uom_silicie_id and record.qty_conversion_silicie \
                    and record.alcoholic_grade and record.absolute_alcohol:
                record.fields_check = True
                if record.silicie_move_type_id == a14_type:
                    a14_move = self.env['stock.move'].search(
                        [('silicie_move_type_id', '=', a14_type.id),
                         ('reference', '=', record.reference),
                         silicie_domain])
                    a15_move = self.env['stock.move'].search(
                        [('silicie_move_type_id', '=', a15_type.id),
                         ('reference', '=', record.reference),
                         silicie_domain],
                        limit=1)
                    a32_move = self.env['stock.move'].search(
                        [('silicie_move_type_id', '=', a32_type.id),
                         ('notes_silice', '=', record.reference),
                         silicie_domain],
                        limit=1)
                    a14_qty = sum(a14_move.mapped('absolute_alcohol')) or 0.0
                    a15_qty = a15_move.absolute_alcohol or 0.0
                    a32_qty = a32_move.absolute_alcohol or 0.0
                    if not record.silicie_processing_id or (not record.silicie_operation_num):
                        record.fields_check = False
                    elif (abs(a15_qty + a32_qty - a14_qty) > 0.005):
                        a14_move.write({'fields_check': False})
                        if a15_move:
                            a15_move.fields_check = False
                        if a32_move:
                            a32_move.fields_check = False
                if record.silicie_move_type_id == a15_type:
                    a14_move = self.env['stock.move'].search(
                        [('silicie_move_type_id', '=', a14_type.id),
                         ('reference', '=', record.reference),
                         silicie_domain])
                    a32_move = self.env['stock.move'].search(
                        [('silicie_move_type_id', '=', a32_type.id),
                         ('notes_silice', '=', record.reference),
                         silicie_domain],
                        limit=1)
                    a14_qty = sum(a14_move.mapped('absolute_alcohol')) or 0.0
                    a32_qty = a32_move.absolute_alcohol or 0.0
                    if not record.silicie_processing_id or (not record.silicie_operation_num):
                        record.fields_check = False
                    elif (abs(record.absolute_alcohol + a32_qty - a14_qty) > 0.005):
                        record.fields_check = False
                        if a14_move:
                            a14_move.write({'fields_check': False})
                        if a32_move:
                            a32_move.fields_check = False
                if record.silicie_move_type_id == a32_type:
                    a14_move = self.env['stock.move'].search(
                        [('silicie_move_type_id', '=', a14_type.id),
                         ('reference', '=', record.notes_silice),
                         silicie_domain])
                    a15_move = self.env['stock.move'].search(
                        [('silicie_move_type_id', '=', a15_type.id),
                         ('reference', '=', record.notes_silice),
                         silicie_domain],
                        limit=1)
                    a14_qty = sum(a14_move.mapped('absolute_alcohol')) or 0.0
                    a15_qty = a15_move.absolute_alcohol or 0.0
                    if not record.silicie_loss_id:
                        record.fields_check = False
                    elif (abs(a15_qty + record.absolute_alcohol - a14_qty) > 0.005):
                        record.fields_check = False
                        if a14_move:
                            a14_move.write({'fields_check': False})
                        if a15_move:
                            a15_move.fields_check = False
            else:
                record.fields_check = False

    @api.multi
    def _send_aeat(self):
        soap_obj = self.env['l10n.es.aeat.soap']
        service = 'IESA1V1Service'
        wsdl = 'https://www3.agenciatributaria.gob.es/static_files/common/internet/dep/aduanas/es/aeat/adsi/lico/ws/v1/altas/alc/IESA1V1.wsdl'
        port_name = 'IESA1V1'
        test = 'S'
        operation = 'IESA1V1'
        message_id = self.env['ir.sequence'].next_by_code('webservice.send.id')
        header = {
            'IdentificadorMensaje': message_id,
            'DatosEstablecimiento':
            {
                'NIFEs': self.env.user.company_id.vat.replace('ES', ''),
                'CAEEs': self.env.user.company_id.cae,
            }
        }
        asientos = []
        for move in self:
            if move.send_silicie or move.not_declare:
                continue

            move.silicie_product_type = move.product_id.product_tmpl_id.silicie_product_type
            if move.silicie_product_type != 'none':
                if move.silicie_product_type == 'alcohol':
                    datos_envase = {
                        'TipoEnvase': move.container_type_silicie_id.code,
                        'CapacidadEnvase': move.factor_conversion_silicie,
                        'NumeroEnvases': int(move.quantity_done),
                    }
                    datos_alcohol = {
                        'GradoAlcoholico': move.alcoholic_grade,
                        'CantidadAbsoluta': move.absolute_alcohol,
                        'DatosEnvase': datos_envase,
                    }
                    datos_producto = {
                        'CodigoEpigrafe': move.epigraph_silicie_id.code,
                        'Clave': move.product_key_silicie_id.code,
                        'CodigoNC': move.nc_code,
                        'Cantidad': move.qty_conversion_silicie,
                        'UnidadMedida': move.uom_silicie_id.code,
                        'DescripcionProducto': move.product_id.name,
                        'RefProducto': move.product_id.default_code,
                        'DatosAlcohol': datos_alcohol,
                    }
                    asiento = {
                        'DatosIdentificativosAsiento': {
                            'NumReferenciaInterno': move.id,
                        },
                        'DatosFecha': {
                            'FechaMovimiento': move.date.strftime('%Y-%m-%d'),
                            'FechaRegistroContable': move.date.strftime('%Y-%m-%d'),
                        },
                        'DatosMovimiento': {
                            'TipoMovimiento':  move.silicie_move_type_id.code,
                            'Regimen': move.silice_tax_position,
                        },
                        'DatosJustificante': {
                            'TipoJustificante': move.silicie_proof_type_id.code,
                            'NumJustificante': move.reference,
                        },
                        'DatosProducto': datos_producto,
                        'Observaciones': move.notes_silice or '',
                    }

                    # Production
                    if move.silicie_move_type_id == self.env.ref('l10n_es_aeat_silicie.aeat_move_type_silicie_a14') or \
                            move.silicie_move_type_id == self.env.ref('l10n_es_aeat_silicie.aeat_move_type_silicie_a15'):
                        asiento['DatosOpeTransformacion'] = {
                            'TipoOpTransformacion': move.silicie_processing_id.code,
                            'NumOpTransformacion': move.silicie_operation_num,
                            'UniFabProcDesc': '',
                            'UniFabProcCod': '',
                        }

                    # Loss
                    if move.silicie_move_type_id == self.env.ref('l10n_es_aeat_silicie.aeat_move_type_silicie_a32') or \
                        move.silicie_move_type_id == self.env.ref('l10n_es_aeat_silicie.aeat_move_type_silicie_a30') or \
                            move.silicie_move_type_id == self.env.ref('l10n_es_aeat_silicie.aeat_move_type_silicie_a28'):
                        asiento['DatosMovimiento']['DiferenciasDeMenos'] = move.silicie_loss_id.code

                    asientos.append(asiento)
        if asientos:
            body = {
                'Asiento': asientos,
            }
            res = soap_obj.send_soap(
                service, wsdl, port_name, move, operation, header, body, message_id)

            if res['IESA1V1Sal']:
                for asiento in res['IESA1V1Sal']['Cuerpo']['Asiento']:
                    datos = asiento['DatosIdentificativosAsiento']
                    move = self.env['stock.move'].browse(
                        int(datos['NumReferenciaInterno']))
                    if move:
                        move.silicie_move_number = datos['NumeroAsiento']
                        move.silicie_entry_type = datos['TipoAsiento']
                        move.date_send_silicie = fields.datetime.now()

            if res['ErrorSalida']:
                raise exceptions.Warning(res)

    @api.multi
    def get_test_mode(self, port_name):
        return port_name
