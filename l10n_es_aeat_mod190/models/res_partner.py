from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    incluir_190 = fields.Boolean(string="Included in mod190", default=False)

    aeat_perception_key_id = fields.Many2one(
        comodel_name="l10n.es.aeat.report.perception.key",
        string="Clave percepción",
        help="Se consignará la clave alfabética que corresponda a las "
        "percepciones de que se trate.",
    )

    aeat_perception_subkey_id = fields.Many2one(
        comodel_name="l10n.es.aeat.report.perception.subkey",
        string="Subclave",
        help="""Tratándose de percepciones correspondientes a las claves
            B, E, F, G, H, I, K y L, deberá consignarse, además, la
            subclave numérica de dos dígitos que corresponda a las
            percepciones de que se trate, según la relación de
            subclaves que para cada una de las mencionadas claves
            figura a continuación.
            En percepciones correspondientes a claves distintas de las
            mencionadas, no se cumplimentará este campo.
            Cuando deban consignarse en el modelo 190
            percepciones satisfechas a un mismo perceptor que
            correspondan a diferentes claves o subclaves de
            percepción, deberán cumplimentarle tantos apuntes o
            registros de percepción como sea necesario, de forma que
            cada uno de ellos refleje exclusivamente los datos de
            percepciones correspondientes a una misma clave y, en
            su caso, subclave.""",
    )

    representante_legal_vat = fields.Char(
        string="NIF representante legal",
        help="""Si el perceptor es menor de 14 años, se consignará en
            este campo el número de identificación fiscal de su
            representante legal (padre, madre o tutor).""",
    )

    a_nacimiento = fields.Char(
        string="Año de nacimiento",
        help="""Se consignarán las cuatro cifras del año de nacimiento del
            perceptor.""",
    )

    ceuta_melilla = fields.Char(
        string="Ceuta o Melilla",
        help="""Se consignará el número 1 en los supuestos en que, por
            tratarse de rentas obtenidas en Ceuta o Melilla con
            derecho a la deducción establecida en el artículo 68.4 de
            la Ley del Impuesto, el pagador hubiera determinado el
            tipo de retención de acuerdo con lo previsto en los
            artículos 80.2 y 95.1, último párrafo, del Reglamento del
            Impuesto.
            En otro caso se hará constar en este campo el número
            cero (0).""",
        default=0,
    )

    situacion_familiar = fields.Selection(
        selection=[
            (
                "1",
                "1 - Soltero, viudo, divorciado o separado con hijos menores"
                " de 18 años o mayores incapacitados",
            ),
            (
                "2",
                "2 - Casado y no separado legalmente y su conyuge no tiene "
                "rentas anuales superiores a la cuantía a la que se refiere "
                "la situación 2ª de las contempladas en el artículo 81.1",
            ),
            ("3", "3 - Distinta de las anteriores."),
        ],
        string="Situación familiar",
        help="""Se hará constar el dígito numérico indicativo de la
            situación familiar del perceptor""",
    )
    nif_conyuge = fields.Char(
        string="NIF del conyuge",
        help="""Solo para percepciones correspondientes a las claves A,
            B.01, B.03 y C.
            Únicamente en el supuesto de que la «SITUACIÓN
            FAMILIAR» del perceptor sea la señalada con el número
            2, se hará constar el número de identificación fiscal de su
            cónyuge.""",
    )
    discapacidad = fields.Selection(
        [
            ("0", "0 - Sin discapacidad o grado de minusvalía inferior al 33 por 100."),
            (
                "1",
                "1 - Grado de minusvalía superior al 33 por 100 e inferior "
                "al 66 por 100.",
            ),
            (
                "2",
                "2 - Grado de minusvalía superior al 33 por 100 e inferior "
                "al 66 por 100, y movilidad reducida.",
            ),
            ("3", "3 - Grado de minusvalía igual o superior al 65 por 100."),
        ],
        string="Disability",
        help="""Solo para percepciones correspondientes a las claves A,
            B.01, B.03 y C.
            Si el perceptor es una persona con discapacidad que tiene
            acreditado un grado de minusvalía igual o superior al 33
            por 100, se hará constar en este campo el código
            numérico indicativo de dicho grado""",
    )

    contrato_o_relacion = fields.Selection(
        [
            ("1", "1 - Contrato o relación de carácter general"),
            ("2", "2 - Contrato o relación inferior al año"),
            (
                "3",
                "3 - Contrato o relación laboral especial de carácter " "dependiente",
            ),
            ("4", "4 - Relación esporádica propia de los trabajadores manuales"),
        ],
        string="Contrato o relacion",
        help="""Solo para percepciones correspondientes a la clave A.
            Tratándose de empleados por cuenta ajena en activo, se
            hará constar el dígito numérico indicativo del tipo de
            contrato o relación existente entre el perceptor y la
            persona o entidad retenedora""",
    )
    movilidad_geografica = fields.Selection(
        [("0", "NO"), ("1", "SI")], string="Movilidad geográfica"
    )

    # Hijos, descendientes y ascendientes

    hijos_y_descendientes_m = fields.Integer(
        string="Menores de 3 años",
        help="""
        Solo para percepciones correspondientes a las claves A,
        B.01, B.03 y C.
        Datos referidos a los hijos y demás descendientes del
        perceptor por los que éste tenga derecho a la aplicación
        del mínimo por descendientes previsto en el artículo 58 de
        la Ley del Impuesto.
        """,
    )
    hijos_y_descendientes_m_entero = fields.Integer(
        string="Menores de 3 años, computados por entero"
    )
    hijos_y_descendientes = fields.Integer(
        string="Resto:",
        help="""
        Solo para percepciones correspondientes a las claves A,
        B.01, B.03 y C.
        Datos referidos a los hijos y demás descendientes del
        perceptor por los que éste tenga derecho a la aplicación
        del mínimo por descendientes previsto en el artículo 58 de
        la Ley del Impuesto.
        """,
    )
    hijos_y_descendientes_entero = fields.Integer(
        string="Resto, computadors por entero"
    )

    hijos_y_desc_discapacidad_mr = fields.Integer(
        string="Hijos y descendientes con discapacidad"
    )
    hijos_y_desc_discapacidad_entero_mr = fields.Integer(
        string="Hijos y descendientes con discapacidad, computados por entero"
    )
    hijos_y_desc_discapacidad_33 = fields.Integer(
        string="Hijos y descendientes con discapacidad del 33%"
    )
    hijos_y_desc_discapacidad_entero_33 = fields.Integer(
        string="Hijos y descendientes con discapacidad del 33%"
        ", computados por entero"
    )
    hijos_y_desc_discapacidad_66 = fields.Integer(
        string="Hijos y descendientes con discapacidad del 66%"
    )
    hijos_y_desc_discapacidad_entero_66 = fields.Integer(
        string="Hijos y descendientes con discapacidad del 66%"
        ", computados por entero"
    )
    ascendientes = fields.Integer(string="Ascendientes menores de 75 años")
    ascendientes_entero = fields.Integer(
        string="Ascendientes menores de 75 años, computados por entero"
    )
    ascendientes_m75 = fields.Integer(string="Ascendientes mayores de 75 años")
    ascendientes_entero_m75 = fields.Integer(
        string="Ascendientes mayores de 75 años, computados por entero"
    )

    ascendientes_discapacidad_33 = fields.Integer(
        string="Ascendientes con discapacidad"
    )
    ascendientes_discapacidad_entero_33 = fields.Integer(
        string="Ascendientes con discapacidad, computados por entero"
    )
    ascendientes_discapacidad_mr = fields.Integer(
        string="Ascendientes con discapacidad de más del 33%"
    )
    ascendientes_discapacidad_entero_mr = fields.Integer(
        string="Ascendientes con discapacidad de más del 33%" ", computados por entero"
    )
    ascendientes_discapacidad_66 = fields.Integer(
        string="Ascendientes con discapacidad de más del 66%"
    )
    ascendientes_discapacidad_entero_66 = fields.Integer(
        string="Ascendientes con discapacidad de más del 66%" ", computados por entero"
    )
    computo_primeros_hijos_1 = fields.Integer(
        string="Cómputo de los 3 primeros hijos",
        help="""CÓMPUTO DE LOS 3 PRIMEROS HIJOS.
            Solo para percepciones correspondientes a las claves A,
            B.01, B.03 y C.
            Datos referidos a la proporción en la que ha sido
            computado a efectos de determinar el tipo de retención
            cada uno de los tres primeros hijos o descendientes del
            perceptor, ordenados de mayor a menor según su edad,
            de acuerdo a los siguientes valores:
            1: Computado por entero
            2: Computado por mitad
            0: En cualquier otro caso.
             """,
    )
    computo_primeros_hijos_2 = fields.Integer(
        string="Cómputo de los 3 primeros hijos (2º)"
    )
    computo_primeros_hijos_3 = fields.Integer(
        string="Cómputo de los 3 primeros hijos (3º)"
    )

    ad_required = fields.Integer(
        "Aditional data required", compute="_compute_ad_required"
    )
    is_aeat_perception_subkey_visible = fields.Boolean(
        compute="_compute_is_aeat_perception_subkey_visible"
    )

    @api.depends("aeat_perception_key_id", "aeat_perception_subkey_id")
    def _compute_ad_required(self):
        for record in self:
            ad_required = record.aeat_perception_key_id.ad_required
            if record.aeat_perception_subkey_id:
                ad_required += record.aeat_perception_subkey_id.ad_required
            record.ad_required = ad_required

    @api.depends("aeat_perception_key_id")
    def _compute_is_aeat_perception_subkey_visible(self):
        for record in self:
            record.is_aeat_perception_subkey_visible = bool(
                record.env["l10n.es.aeat.report.perception.subkey"].search(
                    [
                        (
                            "aeat_perception_key_id",
                            "=",
                            record.aeat_perception_key_id.id,
                        ),
                    ]
                )
            )

    @api.onchange("aeat_perception_key_id")
    def onchange_aeat_perception_key_id(self):
        if self.aeat_perception_key_id:
            self.aeat_perception_subkey_id = False
