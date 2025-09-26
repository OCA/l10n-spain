# Copyright 2025 Binhex - Christian Ramos
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    """Perform the reinitialization of this column based on the company's tax agency
    WARNING: Only 03 case is covered here, so existing export/intra-community/other
    invoices should be changed later.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    key = env.ref("l10n_es_verifactu_oca.verifactu_registration_keys_igic_01")
    atc_agency = env.ref("l10n_es_aeat.aeat_tax_agency_canarias")
    cr.execute(
        "UPDATE account_move SET verifactu_registration_key = %s "
        "WHERE move_type = 'out_refund' AND company_id in "
        "(SELECT id FROM res_company where tax_agency_id = %s)",
        (key.id, atc_agency.id),
    )
    cr.execute(
        "UPDATE account_fiscal_position SET verifactu_tax_key = '03' "
        "WHERE company_id in (SELECT id FROM res_company where tax_agency_id = %s)",
        (atc_agency.id,),
    )
