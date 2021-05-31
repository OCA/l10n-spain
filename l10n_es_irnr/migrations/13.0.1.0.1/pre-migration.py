# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade

xmlid_renames = [
    ("l10n_es_irnr.tax_group_retenciones_24", "l10n_es_irnr.tax_group_irnr_no_ue"),
    ("l10n_es_irnr.tax_group_retenciones_19_irnr", "l10n_es_irnr.tax_group_irnr_ue",),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_xmlids(env.cr, xmlid_renames)
