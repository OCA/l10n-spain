# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import exceptions
from odoo.tests.common import TransactionCase

_logger = logging.getLogger("aeat")
_DATES_MAPPING = [
    # (from1, to1, from2, to2, raise_exception)
    (False, False, False, False, True),
    (False, False, "2023-01-01", False, True),
    (False, False, False, "2023-12-31", True),
    (False, False, "2023-01-01", "2023-12-31", True),
    ("2023-01-01", False, False, False, True),
    ("2023-01-01", False, "2022-01-01", False, True),
    ("2023-01-01", False, "2023-01-01", False, True),
    ("2023-01-01", False, "2024-01-01", False, True),
    ("2023-01-01", False, False, "2022-12-31", False),
    ("2023-01-01", False, False, "2023-01-01", True),
    ("2023-01-01", False, False, "2024-01-01", True),
    ("2023-01-01", False, "2022-01-01", "2022-12-31", False),
    ("2023-01-01", False, "2022-01-01", "2023-01-01", True),
    ("2023-01-01", False, "2022-01-01", "2024-01-01", True),
    (False, "2022-12-31", False, False, True),
    (False, "2022-12-31", "2022-01-01", False, True),
    (False, "2022-12-31", "2022-12-31", False, True),
    (False, "2022-12-31", "2023-01-01", False, False),
    (False, "2022-12-31", False, "2022-01-01", True),
    (False, "2022-12-31", False, "2022-12-31", True),
    (False, "2022-12-31", False, "2023-01-01", True),
    (False, "2022-12-31", "2022-01-01", "2022-12-31", True),
    (False, "2022-12-31", "2022-01-01", "2023-01-01", True),
    (False, "2022-12-31", "2023-01-01", "2024-01-01", False),
    ("2022-01-01", "2022-12-31", False, False, True),
    ("2022-01-01", "2022-12-31", "2022-01-01", False, True),
    ("2022-01-01", "2022-12-31", "2022-12-31", False, True),
    ("2022-01-01", "2022-12-31", "2023-01-01", False, False),
    ("2022-01-01", "2022-12-31", False, "2021-12-31", False),
    ("2022-01-01", "2022-12-31", False, "2022-01-01", True),
    ("2022-01-01", "2022-12-31", False, "2022-12-31", True),
    ("2022-01-01", "2022-12-31", False, "2023-01-01", True),
    ("2022-01-01", "2022-12-31", "2021-01-01", "2021-12-31", False),
    ("2022-01-01", "2022-12-31", "2022-01-01", "2022-06-01", True),
    ("2022-01-01", "2022-12-31", "2022-01-01", "2022-12-31", True),
    ("2022-01-01", "2022-12-31", "2022-06-01", "2022-10-01", True),
    ("2022-01-01", "2022-12-31", "2023-01-01", "2024-01-01", False),
]


class TestL10nEsAeat(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tax_map_model = cls.env["l10n.es.aeat.map.tax"]
        cls.tax_map = cls.tax_map_model.create({"model": 999})

    def _test_map_line_overlap(self, from1, to1, from2, to2, raise_exception):
        self.tax_map.write({"date_from": from1, "date_to": to1})
        vals = {"model": 999, "date_from": from2, "date_to": to2}
        if raise_exception:
            with self.assertRaises(exceptions.UserError):
                self.tax_map_model.create(vals)
            # Weird that the record is created anyway, so we remove it
            self.tax_map_model.search(
                [("model", "=", 999), ("id", "!=", self.tax_map.id)]
            ).unlink()
        else:
            self.tax_map_model.create(vals).unlink()

    def test_map_line_overlaps(self):
        for from1, to1, from2, to2, raise_exception in _DATES_MAPPING:
            _logger.info(
                f"Tax map 1 with date_from {from1} and date_to {to1} against tax map 2 "
                f"with date_from {from2} and date_to {to2}"
            )
            self._test_map_line_overlap(from1, to1, from2, to2, raise_exception)
