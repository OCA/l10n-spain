# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class L10nEsMod190AdditionalDataMixin(models.AbstractModel):
    _name = 'l10n.es.mod190.additional.data.mixin'
    _inherit = 'l10n.es.mod190.mixin'
    _description = 'Mod190 Additional Data Mixin'

    mod190_data = fields.Serialized()
    legal_representative_vat = fields.Char(
        sparse="mod190_data",
        oldname="representante_legal_vat",
        string="NIF representante legal", size=9,
        help='''Si el perceptor es menor de 14 años, se consignará en
            este campo el número de identificación fiscal de su
            representante legal (padre, madre o tutor).''')

    birth_year = fields.Char(
        sparse="mod190_data",
        oldname='a_nacimiento',
        string='Año de nacimiento', size=4,
        help='''Se consignarán las cuatro cifras del año de nacimiento del
            perceptor.''')

    ceuta_melilla = fields.Char(
        sparse="mod190_data",
        string='Ceuta o Melilla', size=1,
        help='''Se consignará el número 1 en los supuestos en que, por
            tratarse de rentas obtenidas en Ceuta o Melilla con
            derecho a la deducción establecida en el artículo 68.4 de
            la Ley del Impuesto, el pagador hubiera determinado el
            tipo de retención de acuerdo con lo previsto en los
            artículos 80.2 y 95.1, último párrafo, del Reglamento del
            Impuesto.
            En otro caso se hará constar en este campo el número
            cero (0).''', default=0)

    family_situation = fields.Selection(
        sparse="mod190_data",
        oldname="situacion_familiar",
        selection=[
            ('1', "1 - Soltero, viudo, divorciado o separado con hijos menores"
                  " de 18 años o mayores incapacitados"),
            ('2', '2 - Casado y no separado legalmente y su conyuge no tiene '
                  'rentas anuales superiores a la cuantía a la que se refiere '
                  'la situación 2ª de las contempladas en el artículo 81.1'),
            ('3', '3 - Distinta de las anteriores.')],
        string='Situación familiar',
        help='''Se hará constar el dígito numérico indicativo de la
            situación familiar del perceptor''')
    spouse_vat = fields.Char(
        sparse="mod190_data",
        oldname="nif_conyuge",
        string='NIF del conyuge', size=15,
        help='''Solo para percepciones correspondientes a las claves A,
            B.01, B.03 y C.
            Únicamente en el supuesto de que la «SITUACIÓN
            FAMILIAR» del perceptor sea la señalada con el número
            2, se hará constar el número de identificación fiscal de su
            cónyuge.''')
    disability = fields.Selection(
        sparse="mod190_data",
        selection=[
            ('0',
             '0 - Sin discapacidad o grado de minusvalía inferior al 33%.'),
            ('1',
             '1 - Grado de minusvalía superior al 33% e inferior al 66%.'),
            ('2', '2 - Grado de minusvalía superior al 33% e inferior '
             'al 66%, y movilidad reducida.'),
            ('3', '3 - Grado de minusvalía igual o superior al 66%.')
        ],
        string='Discapacidad',
        oldname="discapacidad",
        help='''Solo para percepciones correspondientes a las claves A,
            B.01, B.03 y C.
            Si el perceptor es una persona con discapacidad que tiene
            acreditado un grado de minusvalía igual o superior al 33
            por 100, se hará constar en este campo el código
            numérico indicativo de dicho grado''')

    relation_kind = fields.Selection(
        sparse="mod190_data",
        selection=[
            ('1', '1 - Contrato o relación de carácter general'),
            ('2', '2 - Contrato o relación inferior al año'),
            ('3', '3 - Contrato o relación laboral especial de carácter '
                  'dependiente'),
            ('4', '4 - Relación esporádica propia de los trabajadores '
                  'manuales')
        ],
        string='Contrato o relación', size=1,
        oldname="contrato_o_relacion",
        help='''Solo para percepciones correspondientes a la clave A.
            Tratándose de empleados por cuenta ajena en activo, se
            hará constar el dígito numérico indicativo del tipo de
            contrato o relación existente entre el perceptor y la
            persona o entidad retenedora'''
    )
    geographical_mobility = fields.Selection(
        sparse="mod190_data",
        selection=[('0', 'NO'), ('1', 'SI')],
        string='Movilidad geográfica',
        oldname='movilidad_geografica',
    )

    # Hijos, descendientes y ascendientes

    descendants_less_3_years = fields.Integer(
        sparse="mod190_data",
        string='Menores de 3 años',
        oldname="hijos_y_descendientes_m",
        help='''
        Solo para percepciones correspondientes a las claves A,
        B.01, B.03 y C.
        Datos referidos a los hijos y demás descendientes del
        perceptor por los que éste tenga derecho a la aplicación
        del mínimo por descendientes previsto en el artículo 58 de
        la Ley del Impuesto.
        ''')
    descendants_less_3_years_integer = fields.Integer(
        sparse="mod190_data",
        oldname="hijos_y_descendientes_m_entero",
        string='Menores de 3 años, computados por entero')
    descendants = fields.Integer(
        sparse="mod190_data",
        string='Resto:',
        oldname='hijos_y_descendientes',
        help='''
        Solo para percepciones correspondientes a las claves A,
        B.01, B.03 y C.
        Datos referidos a los hijos y demás descendientes del
        perceptor por los que éste tenga derecho a la aplicación
        del mínimo por descendientes previsto en el artículo 58 de
        la Ley del Impuesto.
        ''')
    descendants_integer = fields.Integer(
        sparse="mod190_data",
        oldname="hijos_y_descendientes_entero",
        string='Resto, computadors por entero'
    )
    descendants_disability = fields.Integer(
        oldname="hijos_y_desc_discapacidad_mr", sparse="mod190_data",
        string='Hijos y descendientes con discapacidad')
    descendants_disability_integer = fields.Integer(
        oldname="hijos_y_desc_discapacidad_entero_mr", sparse="mod190_data",
        string='Hijos y descendientes con discapacidad, computados por entero')
    descendants_disability_33 = fields.Integer(
        oldname="hijos_y_desc_discapacidad_33", sparse="mod190_data",
        string='Hijos y descendientes con discapacidad del 33%')
    descendants_disability_33_integer = fields.Integer(
        oldname="hijos_y_desc_discapacidad_entero_33", sparse="mod190_data",
        string='Hijos y descendientes con discapacidad del 33%'
               ', computados por entero')
    descendants_disability_66 = fields.Integer(
        oldname="hijos_y_desc_discapacidad_66", sparse="mod190_data",
        string='Hijos y descendientes con discapacidad del 66%')
    descendants_disability_66_integer = fields.Integer(
        oldname="hijos_y_desc_discapacidad_entero_66", sparse="mod190_data",
        string='Hijos y descendientes con discapacidad del 66%'
               ', computados por entero')
    ancestors = fields.Integer(
        oldname="ascendientes", sparse="mod190_data",
        string='Ascendientes menores de 75 años')
    ancestors_integer = fields.Integer(
        oldname="ascendientes_entero", sparse="mod190_data",
        string='Ascendientes menores de 75 años, computados por entero')
    ancestors_older_75 = fields.Integer(
        oldname="ascendientes_m75", sparse="mod190_data",
        string='Ascendientes mayores de 75 años')
    ancestors_older_75_integer = fields.Integer(
        oldname="ascendientes_entero_m75", sparse="mod190_data",
        string='Ascendientes mayores de 75 años, computados por entero')
    ancestors_disability_33 = fields.Integer(
        oldname="ascendientes_discapacidad_33", sparse="mod190_data",
        string='Ascendientes con discapacidad')
    ancestors_disability_33_integer = fields.Integer(
        oldname="ascendientes_discapacidad_entero_33", sparse="mod190_data",
        string='Ascendientes con discapacidad, computados por entero')
    ancestors_disability = fields.Integer(
        oldname="ascendientes_discapacidad_mr", sparse="mod190_data",
        string='Ascendientes con discapacidad de más del 33%')
    ancestors_disability_integer = fields.Integer(
        oldname="ascendientes_discapacidad_entero_mr", sparse="mod190_data",
        string='Ascendientes con discapacidad de más del 33%'
               ', computados por entero')
    ancestors_disability_66 = fields.Integer(
        oldname="ascendientes_discapacidad_66", sparse="mod190_data",
        string='Ascendientes con discapacidad de más del 66%')
    ancestors_disability_66_integer = fields.Integer(
        oldname="ascendientes_discapacidad_entero_66", sparse="mod190_data",
        string='Ascendientes con discapacidad de más del 66%'
               ', computados por entero')
    calculation_rule_first_childs_1 = fields.Integer(
        string='Cómputo de los 3 primeros hijos', sparse="mod190_data",
        oldname="computo_primeros_hijos_1",
        help='''CÓMPUTO DE LOS 3 PRIMEROS HIJOS.
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
             ''')
    calculation_rule_first_childs_2 = fields.Integer(
        oldname="computo_primeros_hijos_2", sparse="mod190_data",
        string='Cómputo de los 3 primeros hijos (2º)')
    calculation_rule_first_childs_3 = fields.Integer(
        oldname="computo_primeros_hijos_3", sparse="mod190_data",
        string='Cómputo de los 3 primeros hijos (3º)')

    additional_data_required = fields.Integer(
        'Additional data required',
        compute='_compute_additional_data_required'
    )

    @api.depends('aeat_perception_key_id', 'aeat_perception_subkey_id')
    def _compute_additional_data_required(self):
        for record in self:
            data = record.aeat_perception_key_id.additional_data_required
            if record.aeat_perception_subkey_id:
                data += record.aeat_perception_subkey_id.additional_data_required
            record.additional_data_required = data

    @api.model
    def _get_applicable_fields(self):
        return [
            'legal_representative_vat',
            'birth_year',
            'ceuta_melilla',
            'family_situation',
            'spouse_vat',
            'disability',
            'relation_kind',
            'geographical_mobility',
            'descendants_less_3_years',
            'descendants_less_3_years_integer',
            'descendants',
            'descendants_integer',
            'descendants_disability',
            'descendants_disability_integer',
            'descendants_disability_33',
            'descendants_disability_33_integer',
            'descendants_disability_66',
            'descendants_disability_66_integer',
            'ancestors',
            'ancestors_integer',
            'ancestors_older_75',
            'ancestors_older_75_integer',
            'ancestors_disability_33',
            'ancestors_disability_33_integer',
            'ancestors_disability',
            'ancestors_disability_integer',
            'ancestors_disability_66',
            'ancestors_disability_66_integer',
            'calculation_rule_first_childs_1',
            'calculation_rule_first_childs_2',
            'calculation_rule_first_childs_3'
        ]
