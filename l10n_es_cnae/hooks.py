# Copyright 2026 Moduon Team S.L. <info@moduon.team>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3).
"""Migration of CNAE 2009 subclasses to CNAE 2025, offline.

It runs from the ``18.0.2.0.0`` migration script, after ``l10n_eu_nace``
migrates NACE Rev. 2 to NACE Rev. 2.1, and when installing the module.
"""

import csv

from odoo.tools import file_open

from odoo.addons.l10n_eu_nace.hooks import migrate_industries

# CNAE 2009 subclasses whose code disappears or gets another activity in CNAE 2025,
# from INE's correspondence table. When it gives several codes, the one that best
# fits the activity was chosen by hand.
CNAE2009_CNAE2025 = {
    "35.15": "35.12",  # hydroelectric: renewable (35.15 is now trade of electricity)
    "35.16": "35.11",  # conventional thermal: non-renewable (35.16 is now storage)
    "35.17": "35.11",  # nuclear: non-renewable
    "35.18": "35.12",  # wind: renewable
    "35.19": "35.12",  # other types, e.g. solar or biomass: renewable
    "41.21": "41.01",
    "41.22": "41.02",
    "85.43": "85.41",
    "85.44": "85.42",
    "91.05": "91.11",
    "91.06": "91.12",
}

NAMESPACE = "cnae2025"


def read_cnae2025():
    """Return the CNAE 2025 subclasses as ``{code, parent_code, name, name_es,
    nace2_code}``, where ``nace2_code`` is the CNAE 2009 code with the same
    activity, if any."""
    with file_open("l10n_es_cnae/data/res.partner.industry.csv") as csvfile:
        return [
            {
                "code": code,
                "parent_code": parent_code,
                "name": name,
                "name_es": name_es,
                "nace2_code": cnae2009_code,
            }
            for _xmlid, parent_code, code, name, name_es, cnae2009_code in csv.reader(
                csvfile
            )
        ]


def migrate_to_cnae2025(env):
    """Create or update the CNAE 2025 subclasses, replacing the CNAE 2009 ones."""
    rows = read_cnae2025()
    kept = {row["nace2_code"] for row in rows if row["nace2_code"]}
    migrate_industries(
        env,
        rows,
        CNAE2009_CNAE2025,
        kept | set(CNAE2009_CNAE2025),
        "cnae2009",
        NAMESPACE,
    )
    env["res.partner.industry.eu.nace.wizard"].create_spanish_industries()


def post_init_hook(env):
    migrate_to_cnae2025(env)
