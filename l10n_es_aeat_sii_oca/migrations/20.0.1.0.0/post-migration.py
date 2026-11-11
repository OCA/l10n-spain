# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""The SII breakdown and registration keys come now from the Spanish data of the
taxes (core `l10n_es` fields) instead of the SII tax map and the registration
key records. The taxes of databases migrated from older versions keep the
default `l10n_es_type` ('sujeto'), so their data is derived here from the SII
map lines, which is what has been sent to the AEAT."""

import csv
import logging
from collections import Counter, defaultdict

from openupgradelib import openupgrade

from odoo.tools import file_open

from odoo.addons.l10n_es_aeat_sii_oca.models.account_chart_template import (
    IGIC_TAXES_WITHOUT_APPLICABILITY,
)

_logger = logging.getLogger(__name__)

NOT_SUBJECT_CODES = {"SFENS", "SFESNS", "SFRNS"}
GOODS_CODES = {"SFESB", "SFENS", "SFESBE", "SFESISP"}
SERVICE_CODES = {"SFESS", "SFESNS", "SFESSE"}
# Registration key codes whose meaning depends on the use: the core catalog
# suffixes them. The use is the one of the invoice or of the fiscal position
# field, not the type of the old key record (fiscal positions often had the
# sale record 01 as purchase key).
SUFFIXED_KEYS = {
    "sale": {"02", "09", "12", "13", "14", "16"},
    "purchase": {"02", "09", "12", "13", "14"},
}
# Codes of the core catalog that are not valid for purchases
SALE_ONLY_KEYS = {"10", "11", "15", "17"}


def _key_code_sql(alias, use_sql):
    """SQL expression of the core catalog code of a registration key record
    for the given use ('sale' or 'purchase' SQL expression)."""
    whens = " ".join(
        f"WHEN {use_sql} = '{use}' AND {alias}.code IN "
        f"({', '.join(repr(code) for code in sorted(codes))}) "
        f"THEN {alias}.code || '_{use}'"
        for use, codes in SUFFIXED_KEYS.items()
    )
    return f"CASE {whens} ELSE {alias}.code END"


def _type_from_codes(codes):
    """Spanish tax type that gives the same SII breakdown as the map codes."""
    for code, es_type in (
        ("RE", "recargo"),
        ("NotIncludedInTotal", "retencion"),
        ("BaseNotIncludedInTotal", "ignore"),
        ("SFRSA", "sujeto_agricultura"),
        ("SFRND", "no_deducible"),
        ("SFRISP", "sujeto_isp"),
        ("SFESISP", "sujeto_isp"),
        ("SFESBE", "exento"),
        ("SFESSE", "exento"),
    ):
        if code in codes:
            return es_type
    if codes & NOT_SUBJECT_CODES:
        return "no_sujeto_loc"
    if "DUA" in codes:
        return "dua"
    if codes & {"SFESB", "SFESS", "SFRS"}:
        return "sujeto"
    return False


def _template_values():
    """Spanish values of the core es_common tax templates, by template id."""
    fields = ("l10n_es_type", "l10n_es_exempt_reason")
    with file_open("l10n_es/data/template/account.tax-es_common.csv", "r") as file:
        return {
            row["id"]: {field: row.get(field) for field in fields if row.get(field)}
            for row in csv.DictReader(file)
            if row["id"]
        }


def _get_map_codes(env):
    """Return {tax id: set of SII map line codes} of every SII map (the AEAT
    one, which may have the AEAT as tax agency, and the ones of other agencies
    such as the Canary one, whose taxes are different), for the taxes created
    from the chart templates and the ones whose AEAT equivalent tax is one of
    them."""
    if not openupgrade.table_exists(env.cr, "aeat_sii_map_lines"):
        return {}
    env.cr.execute(
        """
        SELECT tax.id, line.code
          FROM aeat_sii_map sii_map
          JOIN aeat_sii_map_lines line ON line.sii_map_id = sii_map.id
          JOIN aeat_sii_map_lines_l10n_es_aeat_map_tax_line_tax_rel rel
            ON rel.aeat_sii_map_lines_id = line.id
          JOIN l10n_es_aeat_map_tax_line_tax xmlid
            ON xmlid.id = rel.l10n_es_aeat_map_tax_line_tax_id
          JOIN ir_model_data imd
            ON imd.module = 'account' AND imd.model = 'account.tax'
           AND imd.name = SPLIT_PART(imd.name, '_', 1) || '_' || xmlid.name
           AND SPLIT_PART(imd.name, '_', 1) ~ '^[0-9]+$'
          JOIN account_tax tax ON tax.id = imd.res_id
        """
    )
    codes = defaultdict(set)
    for tax_id, code in env.cr.fetchall():
        codes[tax_id].add(code)
    if openupgrade.column_exists(env.cr, "account_tax", "aeat_equivalent_tax_id"):
        env.cr.execute(
            """
            SELECT id, aeat_equivalent_tax_id FROM account_tax
             WHERE aeat_equivalent_tax_id IS NOT NULL
            """
        )
        for tax_id, equivalent_id in env.cr.fetchall():
            if equivalent_id in codes:
                codes[tax_id] |= codes[equivalent_id]
    return codes


def _invoice_fiscal_positions(env, tax_id):
    """Return a Counter of the fiscal positions of the posted invoices with the
    tax."""
    env.cr.execute(
        """
        SELECT move.fiscal_position_id, COUNT(DISTINCT move.id)
          FROM account_move_line_account_tax_rel rel
          JOIN account_move_line line ON line.id = rel.account_move_line_id
          JOIN account_move move ON move.id = line.move_id
         WHERE rel.account_tax_id = %s AND move.state = 'posted'
           AND move.move_type IN ('out_invoice', 'out_refund', 'in_invoice',
                                  'in_refund')
         GROUP BY move.fiscal_position_id
        """,
        (tax_id,),
    )
    return Counter(dict(env.cr.fetchall()))


def _fiscal_position_values(env):
    """Return {fiscal position id: (gen type, exempt cause, no taxable cause)}
    with the values the old SII code used."""
    has_exempt = openupgrade.column_exists(
        env.cr, "account_fiscal_position", "sii_exempt_cause"
    )
    has_no_taxable = openupgrade.column_exists(
        env.cr, "account_fiscal_position", "sii_no_taxable_cause"
    )
    env.cr.execute(
        f"""
        SELECT id, sii_partner_identification_type, name->>'es_ES',
               name->>'en_US',
               {"sii_exempt_cause" if has_exempt else "NULL"},
               {"sii_no_taxable_cause" if has_no_taxable else "NULL"}
          FROM account_fiscal_position
        """
    )
    values = {}
    for fp_id, ident, name_es, name_en, exempt, no_taxable in env.cr.fetchall():
        names = {name_es, name_en}
        if ident:
            gen_type = int(ident)
        elif "Régimen Intracomunitario" in names:
            gen_type = 2
        elif "Régimen Extracomunitario" in names:
            gen_type = 3
        else:
            gen_type = 1
        if gen_type == 2:
            exempt = "E5"
        elif exempt == "none":
            exempt = False
        if gen_type == 3 and exempt not in ("E2", "E3"):
            exempt = "E2"
        values[fp_id] = (gen_type, exempt, no_taxable or "ImporteTAIReglasLocalizacion")
    return values


def _most_common(counter, values_by_key):
    """Most used value of the keys of a Counter, ignoring empty values."""
    totals = Counter()
    for key, count in counter.items():
        value = values_by_key(key)
        if value:
            totals[value] += count
    return totals.most_common(1)[0][0] if totals else False


def _no_subject_type(env, tax_id, es_type, fp_values):
    """'no_sujeto' or 'no_sujeto_loc' from the no taxable cause of the fiscal
    positions of the invoices with the tax."""
    cause = _most_common(
        _invoice_fiscal_positions(env, tax_id),
        lambda fp_id: fp_values.get(fp_id, (0, 0, "ImporteTAIReglasLocalizacion"))[2],
    )
    if cause == "ImportePorArticulos7_14_Otros" or (
        not cause and es_type == "no_sujeto"
    ):
        return "no_sujeto"
    return "no_sujeto_loc"


def _exempt_reason(env, tax_id, template, fp_values):
    """Exemption cause of an exempt tax: the template one, else the one that was
    sent with all the fiscal positions of its invoices, when it is not what the
    module derives from the operation type (E5 intra-community, E2 export)."""
    if template.get("l10n_es_exempt_reason"):
        return template["l10n_es_exempt_reason"]
    sent_causes = set()
    derived_causes = set()
    for fp_id in _invoice_fiscal_positions(env, tax_id):
        gen_type, sent_cause = fp_values.get(fp_id, (1, False, False))[:2]
        sent_causes.add(sent_cause or False)
        derived_causes.add({2: "E5", 3: "E2"}.get(gen_type, False))
    if len(sent_causes) == 1 and sent_causes != derived_causes:
        return sent_causes.pop()
    if sent_causes != derived_causes:
        _logger.warning(
            "Exempt tax %s sent with several exemption causes (%s): set the one of "
            "the tax if the cause of the operation type does not fit",
            tax_id,
            ", ".join(sorted(cause or "none" for cause in sent_causes)),
        )
    return False


def _vals_from_map_codes(env, tax, codes, template, fp_values):
    """Spanish data of a tax that gives the breakdown of its SII map codes."""
    vals = {}
    new_type = _type_from_codes(codes)
    if (
        new_type == "sujeto"
        and tax["es_type"] in ("exento", "dua")
        and ("SFRS" in codes)
    ):
        # The same purchase breakdown (DesgloseIVA) as 'sujeto'
        new_type = tax["es_type"]
    if new_type == "no_sujeto_loc":
        new_type = _no_subject_type(env, tax["id"], tax["es_type"], fp_values)
    if new_type and new_type != tax["es_type"]:
        vals["l10n_es_type"] = new_type
    if codes & GOODS_CODES and tax["scope"] != "consu":
        vals["tax_scope"] = "consu"
    elif codes & SERVICE_CODES and tax["scope"] != "service":
        vals["tax_scope"] = "service"
    if tax["use"] == "purchase" and bool(tax["investment"]) != ("SFRBI" in codes):
        vals["l10n_es_bien_inversion"] = "SFRBI" in codes
    if new_type == "exento" and not tax["exempt_reason"]:
        vals["l10n_es_exempt_reason"] = _exempt_reason(
            env, tax["id"], template, fp_values
        )
    return vals


def _vals_without_map_codes(tax, template, ignored):
    """Spanish data of a tax out of the SII map: OSS, template or ignored."""
    vals = {}
    if tax["oss_country"] and tax["use"] == "sale":
        # Distance sales: not subject (location rules), regime 17
        if tax["es_type"] != "no_sujeto_loc":
            vals["l10n_es_type"] = "no_sujeto_loc"
        if not tax["regime_code"]:
            vals["l10n_es_regime_code"] = "17"
    elif template.get("l10n_es_type"):
        if tax["es_type"] != template["l10n_es_type"]:
            vals["l10n_es_type"] = template["l10n_es_type"]
        if template.get("l10n_es_exempt_reason") and not tax["exempt_reason"]:
            vals["l10n_es_exempt_reason"] = template["l10n_es_exempt_reason"]
    elif (
        tax["used"]
        and tax["use"] in ("sale", "purchase")
        and tax["es_type"] != "ignore"
    ):
        # Out of every SII map line: it was not reported
        vals["l10n_es_type"] = "ignore"
        ignored.append(tax["id"])
    return vals


def _migrate_tax_data(env):
    map_codes = _get_map_codes(env)
    templates = _template_values()
    fp_values = _fiscal_position_values(env)
    has_oss = openupgrade.column_exists(env.cr, "account_tax", "oss_country_id")
    env.cr.execute(
        f"""
        SELECT tax.id, tax.type_tax_use AS use, tax.l10n_es_type AS es_type,
               tax.l10n_es_exempt_reason AS exempt_reason, tax.tax_scope AS scope,
               tax.l10n_es_bien_inversion AS investment,
               tax.l10n_es_regime_code AS regime_code,
               {"tax.oss_country_id" if has_oss else "NULL"} AS oss_country,
               SUBSTRING(imd.name FROM '^[0-9]+_(.*)$') AS template_id,
               EXISTS(SELECT 1 FROM account_move_line_account_tax_rel rel
                       WHERE rel.account_tax_id = tax.id) AS used
          FROM account_tax tax
          JOIN res_company company ON company.id = tax.company_id
          JOIN res_country country ON country.id = company.account_fiscal_country_id
          LEFT JOIN ir_model_data imd
            ON imd.module = 'account' AND imd.model = 'account.tax'
           AND imd.res_id = tax.id
         WHERE country.code = 'ES'
        """
    )
    columns = [description[0] for description in env.cr.description]
    taxes = [dict(zip(columns, row, strict=True)) for row in env.cr.fetchall()]
    updates = {}
    ignored = []
    for tax in taxes:
        codes = map_codes.get(tax["id"], set())
        template = templates.get(tax["template_id"], {})
        if codes:
            vals = _vals_from_map_codes(env, tax, codes, template, fp_values)
        else:
            vals = _vals_without_map_codes(tax, template, ignored)
        if vals:
            updates[tax["id"]] = vals
    for tax_id, vals in updates.items():
        columns = ", ".join(f"{field} = %s" for field in vals)
        env.cr.execute(
            f"UPDATE account_tax SET {columns} WHERE id = %s",
            (*vals.values(), tax_id),
        )
    _logger.info("Spanish data derived from the SII map on %s taxes", len(updates))
    if ignored:
        _logger.warning(
            "Taxes used in invoices but in no SII map line, now of type 'ignore' "
            "(not reported, as before): %s",
            ignored,
        )


def _clear_export_code_of_services(env):
    """Services to non-EU customers are not subject: no export key 02 (see the
    chart template override)."""
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_tax tax SET l10n_es_regime_code = NULL
          FROM ir_model_data imd
         WHERE imd.module = 'account' AND imd.model = 'account.tax'
           AND imd.res_id = tax.id
           AND SUBSTRING(imd.name FROM '^[0-9]+_(.*)$')
               = 'account_tax_template_s_iva_e'
           AND tax.l10n_es_regime_code = '02_sale'
        """,
    )


def _set_igic_applicability(env):
    """IGIC taxes without applicability are not for the SII of the AEAT (see the
    chart template override)."""
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_tax tax SET l10n_es_applicability = '03'
          FROM ir_model_data imd
         WHERE imd.module = 'account' AND imd.model = 'account.tax'
           AND imd.res_id = tax.id
           AND SUBSTRING(imd.name FROM '^[0-9]+_(.*)$') IN %s
           AND tax.l10n_es_applicability IS NULL
        """,
        (
            tuple(
                f"account_tax_template_{xml_id}"
                for xml_id in IGIC_TAXES_WITHOUT_APPLICABILITY
            ),
        ),
    )


def _migrate_move_keys(env):
    """The registration keys of the invoices go to the core regime code fields,
    so the posted ones keep what was sent."""
    if not openupgrade.column_exists(env.cr, "account_move", "sii_registration_key"):
        return

    def key_code(column):
        use_sql = (
            "CASE WHEN move.move_type IN ('in_invoice', 'in_refund', 'in_receipt') "
            "THEN 'purchase' ELSE 'sale' END"
        )
        return (
            f"(SELECT {_key_code_sql('k', use_sql)} "
            f"FROM aeat_sii_mapping_registration_keys k WHERE k.id = move.{column})"
        )

    openupgrade.logged_query(
        env.cr,
        f"""
        UPDATE account_move move
           SET l10n_es_regime_code = {key_code("sii_registration_key")},
               l10n_es_regime_code_additional =
                   {key_code("sii_registration_key_additional1")},
               l10n_es_regime_code_additional2 =
                   {key_code("sii_registration_key_additional2")}
         WHERE move.sii_registration_key IS NOT NULL
        """,
    )


def _migrate_fiscal_position_keys(env):
    """A registration key of a fiscal position is kept as forced key only when
    the taxes of the fiscal position do not give it already (01 is the default
    one, 02 comes from the export taxes, 09 from the intra-community acquisition
    ones and 17 from the OSS ones)."""
    if not openupgrade.column_exists(
        env.cr, "account_fiscal_position", "sii_registration_key_sale"
    ):
        return
    env.cr.execute(
        f"""
        SELECT fp.id, {_key_code_sql("sale_key", "'sale'")},
               {_key_code_sql("purchase_key", "'purchase'")}
          FROM account_fiscal_position fp
          LEFT JOIN aeat_sii_mapping_registration_keys sale_key
            ON sale_key.id = fp.sii_registration_key_sale
          LEFT JOIN aeat_sii_mapping_registration_keys purchase_key
            ON purchase_key.id = fp.sii_registration_key_purchase
         WHERE sale_key.id IS NOT NULL OR purchase_key.id IS NOT NULL
        """
    )
    rows = env.cr.fetchall()
    positions = env["account.fiscal.position"].with_context(active_test=False)
    for fp_id, sale_code, purchase_code in rows:
        position = positions.browse(fp_id)
        tax_codes = set(position.tax_ids.mapped("l10n_es_regime_code"))
        vals = {}
        for field, code in (
            ("sii_regime_code_sale", sale_code),
            ("sii_regime_code_purchase", purchase_code),
        ):
            if not code or code == "01" or code in tax_codes:
                continue
            if field == "sii_regime_code_purchase" and code in SALE_ONLY_KEYS:
                _logger.warning(
                    "Fiscal position %s: purchase SII key %s is only valid for "
                    "sales, not kept",
                    fp_id,
                    code,
                )
                continue
            vals[field] = code
        if vals:
            columns = ", ".join(f"{field} = %s" for field in vals)
            env.cr.execute(
                f"UPDATE account_fiscal_position SET {columns} WHERE id = %s",
                (*vals.values(), fp_id),
            )
            _logger.info("Fiscal position %s: forced SII keys %s", fp_id, vals)


def _log_product_exempt_causes(env):
    if not openupgrade.column_exists(env.cr, "product_template", "sii_exempt_cause"):
        return
    env.cr.execute(
        """
        SELECT id, sii_exempt_cause FROM product_template
         WHERE sii_exempt_cause IS NOT NULL AND sii_exempt_cause != 'none'
        """
    )
    rows = env.cr.fetchall()
    if rows:
        _logger.warning(
            "The SII exempt cause of products is gone (the exempt tax gives it); "
            "products that had one: %s",
            rows,
        )


def _migrate_invoice_type(env):
    """The SII invoice type is now the core `l10n_es_invoice_type`, which the
    `l10n_es` migration fills from the core simplified flag (F2/R5 or F1/R4).
    The SII invoices get the type this module used to send instead: the one
    the AEAT holds when the invoice was sent, else the rule of the previous
    version (customs complementary settlement, accounting receipt, specific
    refund type, customer marked for simplified invoices, R1 for the other
    customer refunds). Most invoices sent years ago keep no content, so the
    rule must give what was sent: this module never sent a vendor bill as
    F2, and it sent REAGYP bills as F1 (F6 only for the ones not sent yet).
    The DUA bills keep the F5 of the `l10n_es` migration, as sent."""
    cr = env.cr
    if not openupgrade.column_exists(cr, "account_move", "l10n_es_invoice_type"):
        return
    column = {
        name: openupgrade.column_exists(cr, "account_move", name)
        for name in (
            "sii_lc_operation",
            "sii_is_accounting_receipt",
            "sii_refund_specific_invoice_type",
        )
    }
    lc = "move.sii_lc_operation" if column["sii_lc_operation"] else "FALSE"
    receipt = (
        "move.sii_is_accounting_receipt"
        if column["sii_is_accounting_receipt"]
        else "FALSE"
    )
    specific = (
        "move.sii_refund_specific_invoice_type"
        if column["sii_refund_specific_invoice_type"]
        else "NULL"
    )
    openupgrade.logged_query(
        cr,
        f"""
        UPDATE account_move move
           SET l10n_es_invoice_type = CASE
                   WHEN {lc} THEN 'LC'
                   WHEN move.move_type = 'in_invoice' AND {receipt} THEN 'F6'
                   WHEN move.move_type = 'in_invoice'
                       AND (
                           move.l10n_es_invoice_type = 'F2'
                           OR (
                               move.l10n_es_invoice_type = 'F6'
                               AND move.aeat_state != 'not_sent'
                           )
                       )
                       THEN 'F1'
                   WHEN move.move_type = 'in_invoice'
                       THEN move.l10n_es_invoice_type
                   WHEN move.move_type = 'in_refund'
                       THEN COALESCE({specific}, 'R4')
                   WHEN move.move_type = 'out_invoice'
                       THEN CASE WHEN partner.aeat_simplified_invoice
                                 THEN 'F2' ELSE 'F1' END
                   ELSE COALESCE(
                       {specific},
                       CASE WHEN partner.aeat_simplified_invoice
                            THEN 'R5' ELSE 'R1' END
                   )
               END
          FROM res_partner partner, res_company company
         WHERE partner.id = move.commercial_partner_id
           AND company.id = move.company_id
           AND company.sii_enabled
           AND move.move_type IN
               ('out_invoice', 'out_refund', 'in_invoice', 'in_refund')
        """,
    )
    # What the AEAT holds wins: a modification or a cancellation must keep it.
    # The content is read with a pattern, not as JSON, as old records may hold
    # a Python representation of the dictionary.
    openupgrade.logged_query(
        cr,
        """
        UPDATE account_move move
           SET l10n_es_invoice_type = sent.invoice_type
          FROM (
              SELECT id,
                     substring(
                         aeat_content_sent
                         FROM '[''"]TipoFactura[''"]: *[''"]([A-Z][A-Z0-9])[''"]'
                     ) AS invoice_type
                FROM account_move
               WHERE aeat_content_sent IS NOT NULL
                 AND move_type IN
                     ('out_invoice', 'out_refund', 'in_invoice', 'in_refund')
          ) sent
         WHERE sent.id = move.id
           AND sent.invoice_type IN (
               'F1', 'F2', 'F4', 'F5', 'F6', 'LC',
               'R1', 'R2', 'R3', 'R4', 'R5'
           )
           AND move.l10n_es_invoice_type IS DISTINCT FROM sent.invoice_type
        """,
    )


def _compute_draft_invoice_marks(env):
    """The pre-migration leaves the marks of art. 7.2/7.3 and 6.1.d empty;
    the invoices still in draft get them as new ones do."""
    moves = env["account.move"].search(
        [
            ("state", "=", "draft"),
            ("move_type", "in", ["out_invoice", "out_refund", "in_invoice"]),
            ("company_id.sii_enabled", "=", True),
        ]
    )
    moves._compute_sii_invoice_marks()


@openupgrade.migrate()
def migrate(env, version):
    _migrate_tax_data(env)
    _clear_export_code_of_services(env)
    _set_igic_applicability(env)
    _migrate_move_keys(env)
    _migrate_fiscal_position_keys(env)
    _log_product_exempt_causes(env)
    _migrate_invoice_type(env)
    _compute_draft_invoice_marks(env)
