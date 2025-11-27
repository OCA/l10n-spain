# 2025 Moval Agroingeniería
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import csv
import logging
import os

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    """Load INE codes from CSV file after module installation."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    _load_ine_codes(env)
    _link_cities(env)


def _load_ine_codes(env):
    """Load INE codes from CSV file."""
    # Check if data is already loaded
    if env["res.ine.code"].search_count([]) > 0:
        _logger.info("INE codes already loaded. Skipping...")
        return

    # Get CSV file path
    module_path = os.path.dirname(os.path.dirname(__file__))
    csv_path = os.path.join(module_path, "l10n_es_ine_code", "data", "res.ine.code.csv")

    if not os.path.exists(csv_path):
        _logger.error("CSV file not found: %s", csv_path)
        return

    _logger.info("Loading INE codes from %s", csv_path)

    # Read and load CSV data
    with open(csv_path, "r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        records_to_create = []

        for row in reader:
            # Prepare record data
            record_data = {
                "ine_code_state": row.get("ine_code_state", ""),
                "ine_code_province": int(row["ine_code_province"])
                if row.get("ine_code_province") and row["ine_code_province"].strip()
                else False,
                "ine_code_city": int(row["ine_code_city"])
                if row.get("ine_code_city") and row["ine_code_city"].strip()
                else False,
                "city_name": row.get("city_name", ""),
                "city_name_simplified": row.get("city_name_simplified", ""),
                "city_name_aka": row.get("city_name_aka", ""),
                "city_name_aka_simplified": row.get("city_name_aka_simplified", ""),
                "city_name_reordered": row.get("city_name_reordered", ""),
                "city_name_reordered_simplified": row.get(
                    "city_name_reordered_simplified", ""
                ),
            }
            records_to_create.append(record_data)

            # Create in batches of 500 for better performance
            if len(records_to_create) >= 500:
                env["res.ine.code"].create(records_to_create)
                _logger.info("Created %d INE code records", len(records_to_create))
                records_to_create = []

        # Create remaining records
        if records_to_create:
            env["res.ine.code"].create(records_to_create)
            _logger.info("Created %d INE code records", len(records_to_create))

    _logger.info("INE codes loaded successfully")


def _link_cities(env):
    """Link INE codes with cities from base_location."""
    _logger.info("Linking INE codes with res.city records...")

    # Get Spain country
    spain = env["res.country"].search([("code", "=", "ES")], limit=1)
    if not spain:
        _logger.warning("Spain country not found. Cannot link cities.")
        return

    # Get all INE codes without city_id
    ine_codes = env["res.ine.code"].search([("city_id", "=", False)])
    _logger.info("Found %d INE codes to link", len(ine_codes))

    linked_count = 0
    for ine_code in ine_codes:
        city = False

        # Strategy 1: Exact match with simplified reordered name
        # Handles: "Bonillo, El" -> "EL BONILLO" = "El Bonillo" in res.city
        if ine_code.city_name_reordered_simplified:
            city = env["res.city"].search(
                [
                    ("country_id", "=", spain.id),
                    ("name", "=ilike", ine_code.city_name_reordered_simplified),
                ],
                limit=1,
            )

        # Strategy 2: Exact match with simplified name
        # Handles: "Madrid" -> "MADRID" = "Madrid" in res.city
        if not city and ine_code.city_name_simplified:
            city = env["res.city"].search(
                [
                    ("country_id", "=", spain.id),
                    ("name", "=ilike", ine_code.city_name_simplified),
                ],
                limit=1,
            )

        # Strategy 3: Normalized match (replace hyphens with spaces)
        # Handles: "Corral-Rubio" -> "CORRAL RUBIO" = "Corral Rubio" in res.city
        if not city and ine_code.city_name_simplified:
            normalized_name = ine_code.city_name_simplified.replace("-", " ")
            city = env["res.city"].search(
                [
                    ("country_id", "=", spain.id),
                    ("name", "=ilike", normalized_name),
                ],
                limit=1,
            )

        # Strategy 4: Partial match (for compound names like "Alcoi/Alcoy")
        # Handles: "Alcoy" -> "ALCOY" within "Alcoi/Alcoy" in res.city
        if not city and ine_code.city_name_simplified:
            city = env["res.city"].search(
                [
                    ("country_id", "=", spain.id),
                    ("name", "ilike", ine_code.city_name_simplified),
                ],
                limit=1,
            )

        if city:
            # Bidirectional linking: ine_code -> city AND city -> ine_code
            ine_code.city_id = city.id
            city.ine_code_id = ine_code.id
            linked_count += 1

        # Commit every 100 records to avoid memory issues
        if linked_count % 100 == 0:
            env.cr.commit()
            _logger.info("Linked %d cities so far...", linked_count)

    # Final commit
    env.cr.commit()
    _logger.info("Successfully linked %d INE codes with cities", linked_count)
