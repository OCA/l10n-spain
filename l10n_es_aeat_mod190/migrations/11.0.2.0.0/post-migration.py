# Copyright 2020 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

sparse_field_columns = [
    ('representante_legal_vat', 'legal_representative_vat'),
    ('a_nacimiento', 'birth_year'),
    ('ceuta_melilla', 'ceuta_melilla'),
    ('situacion_familiar', 'family_situation'),
    ('nif_conyuge', 'spouse_vat'),
    ('discapacidad', 'disability'),
    ('contrato_o_relacion', 'relation_kind'),
    ('movilidad_geografica', 'geographical_mobility'),
    ('hijos_y_descendientes_m', 'descendants_less_3_years'),
    ('hijos_y_descendientes_m_entero', 'descendants_less_3_years_integer'),
    ('hijos_y_descendientes', 'descendants'),
    ('hijos_y_descendientes_entero', 'descendants_integer'),
    ('hijos_y_desc_discapacidad_mr', 'descendants_disability'),
    ('hijos_y_desc_discapacidad_entero_mr', 'descendants_disability_integer'),
    ('hijos_y_desc_discapacidad_33', 'descendants_disability_33'),
    ('hijos_y_desc_discapacidad_entero_33', 'descendants_disability_33_integer'),
    ('hijos_y_desc_discapacidad_66', 'descendants_disability_66'),
    ('hijos_y_desc_discapacidad_entero_66', 'descendants_disability_66_integer'),
    ('ascendientes', 'ancestors'),
    ('ascendientes_entero', 'ancestors_integer'),
    ('ascendientes_m75', 'ancestors_older_75'),
    ('ascendientes_entero_m75', 'ancestors_older_75_integer'),
    ('ascendientes_discapacidad_33', 'ancestors_disability_33'),
    ('ascendientes_discapacidad_entero_33', 'ancestors_disability_33_integer'),
    ('ascendientes_discapacidad_mr', 'ancestors_disability'),
    ('ascendientes_discapacidad_entero_mr', 'ancestors_disability_integer'),
    ('ascendientes_discapacidad_66', 'ancestors_disability_66'),
    ('ascendientes_discapacidad_entero_66', 'ancestors_disability_66_integer'),
    ('computo_primeros_hijos_1', 'calculation_rule_first_childs_1'),
    ('computo_primeros_hijos_2', 'calculation_rule_first_childs_2'),
    ('computo_primeros_hijos_3', 'calculation_rule_first_childs_3'),
]

tables = [
    ('res.partner', 'res_partner'),
    ('l10n.es.aeat.mod190.report.line', 'l10n_es_aeat_mod190_report_line'),
]


@openupgrade.migrate()
def migrate(env, version):
    for model, table in tables:
        for old_field, new_field in sparse_field_columns:
            field = False
            if openupgrade.column_exists(env.cr, table, old_field):
                field = old_field
            elif openupgrade.column_exists(env.cr, table, new_field):
                field = new_field
            if not field:
                continue
            env.cr.execute(
                "SELECT id, %s from %s WHERE %s IS NOT NULL" % (
                    field, table, field
                )
            )
            for data in env.cr.fetchall():
                # We need to rewrite the data in order to not lose anything
                env[model].browse(data[0]).write({
                    new_field: data[1]
                })
            # Once all the data has been migrated, we can delete the column
            openupgrade.drop_columns(env.cr, [(table, field)])
