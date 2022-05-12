# Copyright 2020 Javier de las Heras <jheras@alquemy.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, exceptions, fields, models
from .product_product import PRODUCT_TYPES


SILICIE_WDSL_MAPPING = {
    "wsdl": "l10n_es_aeat_silicie.wsdl",
    "service": "l10n_es_aeat_silicie.service",
    "port_name": "l10n_es_aeat_silicie.port_name",
    "operation": "l10n_es_aeat_silicie.operation",
}
TAX_POSITIONS = [
    ("1", "NO SUJETO"),
    ("2", "SUSPENSIVO"),
    ("3", "EXENTO"),
    ("4", "IMPUESTO DEVENGADO TIPO PLENO"),
    ("5", "IMPUESTO DEVENGADO TIPO REDUCIDO"),
    ("6", "IMPUESTO DEVENGADO A TIPO DE CANARIAS"),
]


class StockMove(models.Model):
    _inherit = "stock.move"

    factor_conversion_silicie = fields.Float(
        string="Factor Conversion SILICIE",
    )
    qty_conversion_silicie = fields.Float(
        string="Qty Conversion SILICIE",
        compute="_compute_qty_conversion_silicie",
        store=True,
        digits=(16, 3),
    )
    alcoholic_grade = fields.Float(
        string="Alcoholic Grade",
        digits=(5, 2),
    )
    absolute_alcohol = fields.Float(
        string="Absolute Alcohol",
        compute="_compute_absolute_alcohol",
        store=True,
        digits=(16, 3),
    )
    silicie_product_type = fields.Selection(
        string="SILICIE Product Type",
        selection=PRODUCT_TYPES,
        default="none",
        required=True,
    )
    silice_tax_position = fields.Selection(
        string="SILICIE Tax Position",
        selection=TAX_POSITIONS,
    )
    silicie_move_type_id = fields.Many2one(
        string="Move Type SILICIE",
        comodel_name="aeat.move.type.silicie",
        ondelete="restrict",
    )
    silicie_proof_type_id = fields.Many2one(
        string="Proof Type SILICIE",
        comodel_name="aeat.proof.type.silicie",
        ondelete="restrict",
    )
    silicie_operation_num = fields.Char(
        string="SILICIE Operation Num.",
    )
    silicie_processing_id = fields.Many2one(
        string="Processing SILICIE",
        comodel_name="aeat.processing.silicie",
        ondelete="restrict",
    )
    silicie_loss_id = fields.Many2one(
        string="Loss SILICIE",
        comodel_name="aeat.loss.silicie",
        ondelete="restrict",
    )
    nc_code = fields.Char(
        string="NC Code",
    )
    silicie_move_number = fields.Char(
        string="SILICIE Move Number",
        copy=False,
    )
    silicie_entry_type = fields.Selection(
        string="SILICIE Entry Type",
        selection=[
            ("1", "Alta de Asiento"),
            ("2", "Anulación de Asiento"),
        ],
    )
    product_key_silicie_id = fields.Many2one(
        string="Product Key SILICIE",
        comodel_name="aeat.product.key.silicie",
        ondelete="restrict",
    )
    container_type_silicie_id = fields.Many2one(
        string="Container Type SILICIE",
        comodel_name="aeat.container.type.silicie",
        ondelete="restrict",
    )
    epigraph_silicie_id = fields.Many2one(
        string="Epigraph SILICIE",
        comodel_name="aeat.epigraph.silicie",
        ondelete="restrict",
    )
    uom_silicie_id = fields.Many2one(
        string="UoM SILICIE",
        comodel_name="aeat.uom.silicie",
        ondelete="restrict",
    )
    send_silicie = fields.Boolean(
        string="Send SILICIE",
        readonly=True,
        store=True,
        compute="_compute_send_silicie",
    )
    not_declare = fields.Boolean(
        string="Not Declare",
        copy=False,
    )
    date_send_silicie = fields.Datetime(
        string="Date Send SILICIE",
        readonly=True,
        copy=False,
    )
    fiscal_position_id = fields.Many2one(
        string="Fiscal Position",
        comodel_name="account.fiscal.position",
        ondelete="restrict",
    )
    notes_silice = fields.Char(
        string="Notes Silice",
        copy=False,
    )
    fields_check = fields.Boolean(
        string="Check Fields",
        copy=False,
    )
    density = fields.Float(
        string="Densidad SILICIE",
        digits=(3, 3),
    )

    @api.depends("date_send_silicie")
    def _compute_send_silicie(self):
        for record in self:
            record.send_silicie = record.date_send_silicie

    @api.depends("factor_conversion_silicie", "product_uom_qty")
    def _compute_qty_conversion_silicie(self):
        for record in self:
            record.qty_conversion_silicie = record.product_uom_qty * \
                record.factor_conversion_silicie

    @api.depends("qty_conversion_silicie", "alcoholic_grade")
    def _compute_absolute_alcohol(self):
        for record in self:
            record.absolute_alcohol = (
                record.alcoholic_grade * record.qty_conversion_silicie) / 100

    @api.multi
    def generate_silicie_fields(self):
        for move in self:
            product_type = move.product_id.silicie_product_type
            if move.send_silicie or move.not_declare or product_type == "none":
                continue
            is_silicie_move = False
            usage = move.location_id.usage
            dest_usage = move.location_dest_id.usage
            # Sale
            if usage == "internal" and dest_usage == "customer":
                is_silicie_move = True
                if product_type == "alcohol":
                    move.silicie_proof_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_proof_type_silicie_j05")
                elif product_type == "beer":
                    move.silicie_proof_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_proof_type_silicie_j03")
                if (not move.fiscal_position_id or move.fiscal_position_id.
                        silicie_partner_identification_type == "national"):
                    move.silicie_move_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a08")
                    move.silice_tax_position = "4"
                elif (move.fiscal_position_id.
                        silicie_partner_identification_type == "canarias"):
                    move.silicie_move_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a09")
                    move.silice_tax_position = "6"
                elif (move.fiscal_position_id.
                        silicie_partner_identification_type == "intra"):
                    move.silicie_move_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a10")
                elif (move.fiscal_position_id.
                        silicie_partner_identification_type == "export"):
                    move.silicie_move_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a11")
            # Sale Refund
            elif usage == "customer" and dest_usage == "internal":
                is_silicie_move = True
                if product_type == "alcohol":
                    move.silicie_proof_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_proof_type_silicie_j05")
                elif product_type == "beer":
                    move.silicie_proof_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_proof_type_silicie_j03")
                if (not move.fiscal_position_id or move.fiscal_position_id.
                        silicie_partner_identification_type == "national"):
                    move.silicie_move_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a02")
                    move.silice_tax_position = "4"
                elif (move.fiscal_position_id.
                        silicie_partner_identification_type == "canarias"):
                    move.silicie_move_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a03")
                    move.silice_tax_position = "6"
                elif (move.fiscal_position_id.
                        silicie_partner_identification_type == "intra"):
                    move.silicie_move_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a04")
                elif (move.fiscal_position_id.
                        silicie_partner_identification_type == "export"):
                    move.silicie_move_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a06")
            # Purchase
            elif usage == "supplier" and dest_usage == "internal":
                is_silicie_move = True
                if product_type == "alcohol":
                    move.silicie_proof_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_proof_type_silicie_j01")
                elif product_type == "beer":
                    move.silicie_proof_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_proof_type_silicie_j03")
                move.reference = \
                    move.purchase_line_id.order_id.arc or move.reference
                if (not move.fiscal_position_id or move.fiscal_position_id.
                        silicie_partner_identification_type == "national"):
                    move.silicie_move_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a02")
                    move.silice_tax_position = "1"
                elif (move.fiscal_position_id.
                        silicie_partner_identification_type == "canarias"):
                    move.silicie_move_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a03")
                elif (move.fiscal_position_id.
                        silicie_partner_identification_type == "intra"):
                    move.silicie_move_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a04")
                elif (move.fiscal_position_id.
                        silicie_partner_identification_type == "export"):
                    move.silicie_move_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a06")
            # Purchase Refund
            elif usage == "internal" and dest_usage == "supplier":
                is_silicie_move = True
                if product_type == "alchohol":
                    move.silicie_proof_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_proof_type_silicie_j05")
                elif product_type == "beer":
                    move.silicie_proof_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_proof_type_silicie_j03")
                if (not move.fiscal_position_id or move.fiscal_position_id.
                        silicie_partner_identification_type == "national"):
                    move.silicie_move_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a08")
                    move.silice_tax_position = "1"
                elif (move.fiscal_position_id.
                        silicie_partner_identification_type == "canarias"):
                    move.silicie_move_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a09")
                elif (move.fiscal_position_id.
                        silicie_partner_identification_type == "intra"):
                    move.silicie_move_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a10")
                elif (move.fiscal_position_id.
                        silicie_partner_identification_type == "export"):
                    move.silicie_move_type_id = self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a11")
            if is_silicie_move:
                move.silicie_product_type = \
                    move.product_id.product_tmpl_id.silicie_product_type
                move.factor_conversion_silicie = \
                    move.product_id.product_tmpl_id.\
                    factor_conversion_silicie
                move.alcoholic_grade = \
                    move.product_id.product_tmpl_id.alcoholic_grade
                move.nc_code = move.product_id.product_tmpl_id.nc_code[:8]
                move.product_key_silicie_id = \
                    move.product_id.product_tmpl_id.\
                    product_key_silicie_id
                move.container_type_silicie_id = \
                    move.product_id.product_tmpl_id.\
                    container_type_silicie_id
                move.epigraph_silicie_id = \
                    move.product_id.product_tmpl_id.epigraph_silicie_id
                move.uom_silicie_id = \
                    move.product_id.product_tmpl_id.uom_silicie_id
                move.fiscal_position_id = \
                    move.picking_id.partner_id.\
                    property_account_position_id
                # Check if all fields have been correctly generated
                move.check_silicie_fields()

    @api.multi
    def clear_silicie_fields(self):
        for move in self:
            move.silicie_product_type = "none"
            move.factor_conversion_silicie = 0
            move.alcoholic_grade = 0
            move.nc_code = ""
            move.product_key_silicie_id = False
            move.container_type_silicie_id = False
            move.epigraph_silicie_id = False
            move.uom_silicie_id = False
            move.fiscal_position_id = False
            move.silicie_proof_type_id = False
            move.silicie_move_type_id = False
            move.silicie_processing_id = False
            move.silicie_loss_id = False
            move.notes_silice = ""

    def _action_done(self):
        move = super()._action_done()
        move.generate_silicie_fields()
        return move

    @api.model
    def cron_generate_silicie_fields(self):
        Move = self.env["stock.move"]
        moves = Move.search([
            ("state", "=", "done"),
            ("silicie_product_type", "!=", False),
            ("date_send_silicie", "=", False)])
        moves.generate_silicie_fields()
        moves = Move.search([
            ("state", "=", "done"),
            ("silicie_product_type", "!=", False)])
        moves.check_silicie_fields()
        return

    @api.model
    def _get_fields_to_check(self):
        if self.product_id.product_class in ["raw", "raw_without_extract"]:
            return [
                "silice_tax_position", "silicie_proof_type_id",
                "product_key_silicie_id",
                "uom_silicie_id", "qty_conversion_silicie",
                "alcoholic_grade", "absolute_alcohol",
            ]
        elif self.product_id.product_class == "":
            return [
                "silice_tax_position", "silicie_proof_type_id",
                "product_key_silicie_id",
                "uom_silicie_id", "qty_conversion_silicie",
                "alcoholic_grade", "absolute_alcohol",
            ]
        elif self.product_id.product_class == "manufactured":
            return [
                "silice_tax_position", "silicie_proof_type_id",
                "uom_silicie_id", "qty_conversion_silicie",
                "alcoholic_grade", "absolute_alcohol",
            ]
        else:
            return [
                "silice_tax_position", "silicie_proof_type_id",
                "epigraph_silicie_id", "container_type_silicie_id",
                "uom_silicie_id", "qty_conversion_silicie",
                "alcoholic_grade", "absolute_alcohol",
            ]

    @api.multi
    def check_silicie_fields(self):
        Move = self.env["stock.move"]
        a14_type = self.env.ref(
            "l10n_es_aeat_silicie.aeat_move_type_silicie_a14")
        a15_type = self.env.ref(
            "l10n_es_aeat_silicie.aeat_move_type_silicie_a15")
        a32_type = self.env.ref(
            "l10n_es_aeat_silicie.aeat_move_type_silicie_a32")
        silicie_domain = ("state", "=", "done")
        for move in self:
            if not all(getattr(move, field_to_check, False)
                       for field_to_check in move._get_fields_to_check()):
                move.fields_check = True
                if move.silicie_move_type_id == a14_type:
                    a14_move = Move.search([
                        ("silicie_move_type_id", "=", a14_type.id),
                        ("reference", "=", move.reference),
                        silicie_domain])
                    a15_move = Move.search([
                        ("silicie_move_type_id", "=", a15_type.id),
                        ("reference", "=", move.reference),
                        silicie_domain],
                        limit=1)
                    a32_move = Move.search([
                        ("silicie_move_type_id", "=", a32_type.id),
                        ("notes_silice", "=", move.reference),
                        silicie_domain], limit=1)
                    a14_qty = sum(a14_move.mapped("absolute_alcohol")) or 0.0
                    a15_qty = a15_move.absolute_alcohol or 0.0
                    a32_qty = a32_move.absolute_alcohol or 0.0
                    if not move.silicie_processing_id or not \
                            move.silicie_operation_num:
                        move.fields_check = False
                    elif abs(a15_qty + a32_qty - a14_qty) > 0.005:
                        a14_move.write({"fields_check": False})
                        if a15_move:
                            a15_move.fields_check = False
                        if a32_move:
                            a32_move.fields_check = False
                if move.silicie_move_type_id == a15_type:
                    a14_move = Move.search([
                        ("silicie_move_type_id", "=", a14_type.id),
                        ("reference", "=", move.reference),
                        silicie_domain])
                    a32_move = Move.search([
                        ("silicie_move_type_id", "=", a32_type.id),
                        ("notes_silice", "=", move.reference),
                        silicie_domain], limit=1)
                    a14_qty = sum(a14_move.mapped("absolute_alcohol")) or 0.0
                    a32_qty = a32_move.absolute_alcohol or 0.0
                    if not move.silicie_processing_id or not \
                            move.silicie_operation_num:
                        move.fields_check = False
                    elif abs(move.absolute_alcohol + a32_qty - a14_qty) > 0.005:
                        move.fields_check = False
                        if a14_move:
                            a14_move.write({"fields_check": False})
                        if a32_move:
                            a32_move.fields_check = False
                if move.silicie_move_type_id == a32_type:
                    a14_move = Move.search([
                        ("silicie_move_type_id", "=", a14_type.id),
                        ("reference", "=", move.notes_silice),
                        silicie_domain])
                    a15_move = Move.search([
                        ("silicie_move_type_id", "=", a15_type.id),
                        ("reference", "=", move.notes_silice),
                        silicie_domain], limit=1)
                    a14_qty = sum(a14_move.mapped("absolute_alcohol")) or 0.0
                    a15_qty = a15_move.absolute_alcohol or 0.0
                    if not move.silicie_loss_id:
                        move.fields_check = False
                    elif abs(a15_qty + move.absolute_alcohol - a14_qty) > 0.005:
                        move.fields_check = False
                        if a14_move:
                            a14_move.write({"fields_check": False})
                        if a15_move:
                            a15_move.fields_check = False
            else:
                move.fields_check = False

    @api.model
    def _get_wsdl_params(self):
        config_object = self.env["ir.config_parameter"].sudo()
        result = {}
        for item in SILICIE_WDSL_MAPPING.keys():
            result[item] = config_object.get_param(
                SILICIE_WDSL_MAPPING[item], False)
        return result

    @api.model
    def _get_silicie_header(self):
        cae = self.env.user.company_id.cae
        if self.env.user.company_id.silicie_test:
            cae = self.env.user.company_id.cae_for_tests
        return {
            "DatosEstablecimiento":
                {
                    "NIFEs": self.env.user.company_id.vat.replace("ES", ""),
                    "CAEEs": cae,
                }
        }

    @api.multi
    def _send_aeat(self):
        soap_obj = self.env["l10n.es.aeat.soap"]
        params = self._get_wsdl_params()
        header = self._get_silicie_header()
        message_id = self.env["ir.sequence"].next_by_code(
            "webservice.send.id")
        header.update({"IdentificadorMensaje": message_id})
        asientos = []
        for move in self:
            if move.send_silicie or move.not_declare:
                continue
            move.silicie_product_type = \
                move.product_id.product_tmpl_id.silicie_product_type
            if move.silicie_product_type:
                datos_envase = ""
                if move.silicie_product_type == "alcohol" or \
                        move.silicie_product_type == "beer":
                    tipo_envase = move.container_type_silicie_id.code or ""
                    capacidad_envase = move.factor_conversion_silicie
                    numero_envases = round(move.quantity_done)
                    if not tipo_envase:
                        capacidad_envase = ""
                        numero_envases = ""
                    datos_envase = {
                        "TipoEnvase": tipo_envase,
                        "CapacidadEnvase": capacidad_envase,
                        "NumeroEnvases": numero_envases,
                    }
                datos_alcohol = {
                    "GradoAlcoholico": move.alcoholic_grade,
                    "CantidadAbsoluta": move.absolute_alcohol,
                    "DatosEnvase": datos_envase,
                }
                datos_producto = {
                    "CodigoEpigrafe": move.epigraph_silicie_id.code or "",
                    "Clave": move.product_key_silicie_id.code or "",
                    "CodigoNC": move.nc_code[:8],
                    "Cantidad": move.qty_conversion_silicie,
                    "UnidadMedida": move.uom_silicie_id.code,
                    "DescripcionProducto": move.product_id.name,
                    "RefProducto": move.product_id.default_code,
                    "DatosAlcohol": datos_alcohol,
                    "EpigrafeFiscal":
                        move.epigraph_silicie_id.fiscal_epigraph_silicie,
                }
                asiento = {
                    "DatosIdentificativosAsiento": {
                        "NumReferenciaInterno": move.id,
                    },
                    "DatosFecha": {
                        "FechaMovimiento": move.date.strftime("%Y-%m-%d"),
                        "FechaRegistroContable": move.date.strftime("%Y-%m-%d"),
                    },
                    "DatosMovimiento": {
                        "TipoMovimiento":  move.silicie_move_type_id.code,
                        "Regimen": move.silice_tax_position,
                    },
                    "DatosJustificante": {
                        "TipoJustificante": move.silicie_proof_type_id.code,
                        "NumJustificante": move.reference,
                    },
                    "DatosProducto": datos_producto,
                    "Observaciones": move.notes_silice or "",
                }

                # Production
                if move.silicie_move_type_id == self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a14") or \
                        move.silicie_move_type_id == self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a15"):
                    asiento["DatosOpeTransformacion"] = {
                        "TipoOpTransformacion": move.silicie_processing_id.code,
                        "NumOpTransformacion": move.silicie_operation_num,
                        "UniFabProcDesc": "",
                        "UniFabProcCod": "",
                    }
                # Loss
                if move.silicie_move_type_id == self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a32") or \
                        move.silicie_move_type_id == self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a30") or \
                        move.silicie_move_type_id == self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a28") or \
                        move.silicie_move_type_id == self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a14") or \
                        move.silicie_move_type_id == self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a39") or \
                        move.silicie_move_type_id == self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a41") or \
                        move.silicie_move_type_id == self.env.ref(
                        "l10n_es_aeat_silicie.aeat_move_type_silicie_a29"):
                    asiento["DatosMovimiento"]["DiferenciasDeMenos"] = \
                        move.silicie_loss_id.code
                asientos.append(asiento)
        if asientos:
            body = {
                "Asiento": asientos,
            }
            res = soap_obj.send_soap(params["service"], params["wsdl"],
                                     params["port_name"], move,
                                     params["operation"], header, body,
                                     message_id)
            if res["IESA1V1Sal"]:
                for asiento in res["IESA1V1Sal"]["Cuerpo"]["Asiento"]:
                    datos = asiento["DatosIdentificativosAsiento"]
                    move = self.env["stock.move"].browse(
                        int(datos["NumReferenciaInterno"]))
                    if move:
                        move.silicie_move_number = datos["NumeroAsiento"]
                        move.silicie_entry_type = datos["TipoAsiento"]
                        move.date_send_silicie = fields.datetime.now()
            if res["ErrorSalida"]:
                raise exceptions.Warning(res)

    @api.multi
    def get_test_mode(self, port_name):
        return port_name

    @api.multi
    def _get_data_dict(self):
        self.ensure_one()
        container_code = self.container_type_silicie_id.code or ""
        factor_conversion = self.factor_conversion_silicie
        qty_done = round(self.quantity_done)
        if not container_code:
            factor_conversion = ""
            qty_done = ""
        return {
            "partner_name":
                self.picking_id.partner_id.name or
                self.company_id.name or "",
            "density": self.density or "",
            "alcoholic_grade": self.alcoholic_grade or "",
            "absolute_alcohol": self.absolute_alcohol or "",
            "container_code": container_code,
            "factor_conversion": factor_conversion,
            "qty_done": qty_done}

    @api.multi
    def _prepare_values(self):
        self.ensure_one()
        data = self._get_data_dict()
        grado_plato = ""
        absolute_alcohol = data["absolute_alcohol"]
        if "grado_plato" in data:
            grado_plato = data.get("grado_plato", "")
        if self.product_id.silicie_product_type in ["beer"]:
            absolute_alcohol = ''
        return {
            "Número Referencia Interno": self.id,
            "Número Asiento Previo": "",
            "Fecha Movimiento": self.date.strftime("%d/%m/%Y"),
            "Fecha Registro Contable": self.date.strftime("%d/%m/%Y"),
            "Tipo Movimiento": self.silicie_move_type_id.code,
            "Información adicional Diferencia en Menos":
                self.silicie_loss_id.code if self.silicie_loss_id else "",
            "Régimen Fiscal": self.silice_tax_position,
            "Tipo de Operación":
                self.silicie_processing_id.code if
                self.silicie_processing_id else "",
            "Número Operación":
                self.silicie_operation_num if
                self.silicie_operation_num else "",
            "Descripción Unidad de Fabricación": "",
            "Código Unidad de Fabricación": "",
            "Tipo Justificante": self.silicie_proof_type_id.code,
            "Número Justificante": self.reference,
            "Tipo Documento Identificativo": "1",
            "Número Documento Identificativo":
                self.picking_id.partner_id.vat or
                self.company_id.vat or "",
            "Razón Social": data["partner_name"][:125],
            "CAE/Número Seed": "",
            "Repercusión Tipo Documento Identificativo": "",
            "Repercusión Número Documento Identificativo": "",
            "Repercusión Razón Social": "",
            "Epígrafe": self.epigraph_silicie_id.fiscal_epigraph_silicie or "",
            "Código Epígrafe": self.epigraph_silicie_id.code or "",
            "Código NC": self.nc_code[:8],
            "Clave": self.product_key_silicie_id.code or "",
            "Cantidad": self.qty_conversion_silicie,
            "Unidad de Medida": self.uom_silicie_id.code,
            "Descripción de Producto": self.product_id.name.strip(),
            "Referencia Producto": self.product_id.default_code,
            "Densidad": data['density'],
            "Grado Alcohólico": data["alcoholic_grade"],
            "Cantidad de Alcohol Puro": absolute_alcohol,
            "Porcentaje de Extracto": "",
            "Kg. - Extracto": "",
            "Grado Plato Medio": grado_plato,
            "Grado Acético": "",
            "Tipo de Envase": data["container_code"],
            "Capacidad de Envase": data["factor_conversion"],
            "Número de Envases": data["qty_done"],
            "Observaciones": self.notes_silice or "",
        }

    @api.multi
    def _get_move_fields(self):
        return {
            "silicie_move_type_id": self.silicie_move_type_id.id,
            "silicie_loss_id": self.silicie_loss_id.id,
            "silice_tax_position": self.silice_tax_position,
            "silicie_processing_id": self.silicie_processing_id.id,
            "silicie_operation_num": self.silicie_operation_num,
            "silicie_proof_type_id": self.silicie_proof_type_id.id,
            "epigraph_silicie_id": self.epigraph_silicie_id.id,
            "nc_code": self.nc_code[:8],
            "product_key_silicie_id": self.product_key_silicie_id.id,
            "uom_silicie_id": self.uom_silicie_id.id,
            "container_type_silicie_id": self.container_type_silicie_id.id,
            "factor_conversion_silicie": self.factor_conversion_silicie,
            "notes_silice": self.notes_silice,
            "alcoholic_grade": self.alcoholic_grade,
            "density": self.density,
        }

    @api.multi
    def open_silicie_move(self):
        self.ensure_one()
        wizard = self.env["silicie.move.editor"].create(
            self._get_move_fields())
        action = self.env.ref(
            "l10n_es_aeat_silicie.action_silicie_edit_move").read()[0]
        action["res_id"] = wizard.id
        return action
