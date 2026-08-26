# Copyright 2026 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
from datetime import date

from odoo import fields
from odoo.tests.common import TransactionCase

from . import sample_files


class TestSiltra(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.siltra_leave_type_id = cls.env["hr.leave.type"].create(
            {
                "name": "Siltra Leave Type",
                "time_type": "leave",
                "requires_allocation": "no",
            }
        )
        cls.extra_leave_type = cls.env["hr.leave.type"].create(
            {
                "name": "Extra Leave Type",
                "time_type": "leave",
                "requires_allocation": "no",
                "leave_validation_type": "hr",
            }
        )
        cls.env["res.company.seguridad.social"].create(
            {
                "company_id": cls.company.id,
                "ss_number": "111111111111111",
            }
        )
        cls.employee_01 = cls.env["hr.employee"].create(
            {
                "name": "Test Employee 01",
                "company_id": cls.company.id,
                "ssnid": "111111111111",
            }
        )
        cls.employee_02 = cls.env["hr.employee"].create(
            {
                "name": "Test Employee 02",
                "company_id": cls.company.id,
                "ssnid": "111111111112",
            }
        )
        cls.employee_03 = cls.env["hr.employee"].create(
            {
                "name": "Test Employee 03",
                "company_id": cls.company.id,
                "ssnid": "111111111113",
            }
        )
        cls.employee_04 = cls.env["hr.employee"].create(
            {
                "name": "Test Employee 04",
                "company_id": cls.company.id,
                "ssnid": "111111111114",
            }
        )

    def make_file(self, date, items):
        file_content = []
        file_content.append(
            sample_files.SILTRA_HEADER.format(file_date=date.strftime("%Y%m%d%H%M"))
        )
        for item in items:
            file_content.append(
                sample_files.SILTRA_COMPANY.format(
                    company_ssid=item["employee_id"]
                    .company_id.ss_number_ids[0]
                    .ss_number
                )
            )
            file_content.append(
                sample_files.SILTRA_EMPLOYEE.format(
                    employee_ssid=item["employee_id"].ssnid
                )
            )
            if item["type"] == "DIT":
                file_content.append(
                    sample_files.SILTRA_DIT.format(
                        start_date=item["date"].strftime("%Y%m%d"),
                        recaida="S" if item.get("recaida", False) else "N",
                        process_start_date=item.get("process_start_date")
                        and item["process_start_date"].strftime("%Y%m%d")
                        or "00000000",
                        previous_process_end_date=item.get("previous_process_end_date")
                        and item["previous_process_end_date"].strftime("%Y%m%d")
                        or "00000000",
                        end_date=item.get("end_date")
                        and item["end_date"].strftime("%Y%m%d")
                        or "00000000",
                        last_review=item.get("last_review")
                        and item["last_review"].strftime("%Y%m%d")
                        or "00000000",
                        next_date=item.get("next_date")
                        and item["next_date"].strftime("%Y%m%d")
                        or "00000000",
                    )
                )
                if not item.get("end_date"):
                    file_content.append(
                        sample_files.SILTRA_CIT.format(
                            next_date=(item["next_date"]).strftime("%Y%m%d")
                        )
                    )
            if item["type"] == "NAC":
                file_content.append(
                    sample_files.SILTRA_NAC.format(date=item["date"].strftime("%Y%m%d"))
                )
            if item["type"] == "DIP":
                file_content.append(
                    sample_files.SILTRA_DIP.format(date=item["date"].strftime("%Y%m%d"))
                )
            if item["type"] == "JUB":
                file_content.append(
                    sample_files.SILTRA_JUB.format(date=item["date"].strftime("%Y%m%d"))
                )
        file_content.append(
            sample_files.SILTRA_FOOTER.format(file_date=date.strftime("%Y%m%d%H%M"))
        )
        return ("\n".join(file_content)).encode("utf-8")

    def test_CIT_with_birth(self):
        siltra_file = self.env["hr.siltra"].create(
            {
                "name": "Test File",
                "file": base64.b64encode(
                    self.make_file(
                        fields.Datetime.now(),
                        [
                            {
                                "employee_id": self.employee_01,
                                "type": "DIT",
                                "date": date(2025, 12, 29),
                                "end_date": date(2026, 1, 26),
                            },
                            {
                                "employee_id": self.employee_01,
                                "type": "NAC",
                                "date": date(2025, 12, 27),
                            },
                        ],
                    )
                ),
            }
        )
        siltra_file.process()
        self.assertEqual(siltra_file.nac_items, 1)
        self.assertEqual(siltra_file.dit_items, 1)
        self.assertEqual(siltra_file.dip_items, 0)
        self.assertEqual(siltra_file.jub_items, 0)
        self.assertEqual(siltra_file.state, "processed")
        self.assertEqual(len(siltra_file.item_ids), 2)
        leave = self.env["hr.leave"].search([("employee_id", "=", self.employee_01.id)])
        self.assertEqual(len(leave), 1)
        self.assertEqual(leave.employee_id, self.employee_01)
        self.assertEqual(2, len(siltra_file.item_ids))
        self.assertEqual(
            siltra_file.item_ids.filtered(lambda i: i.process_type == "DIT").leave_id,
            leave,
        )
        self.assertTrue(
            siltra_file.item_ids.filtered(lambda i: i.process_type == "NAC")
        )

    def test_chained_files(self):
        siltra_file = self.env["hr.siltra"].create(
            {
                "name": "Test File",
                "file": base64.b64encode(
                    self.make_file(
                        fields.Datetime.now(),
                        [
                            {
                                "employee_id": self.employee_01,
                                "type": "DIT",
                                "date": date(2025, 12, 29),
                                "next_date": date(2026, 1, 26),
                            },
                        ],
                    )
                ),
            }
        )
        siltra_file.process()
        self.assertEqual(siltra_file.state, "validated")
        leave = self.env["hr.leave"].search([("employee_id", "=", self.employee_01.id)])
        self.assertEqual(len(leave), 1)
        self.assertEqual(leave.employee_id, self.employee_01)
        self.assertEqual(1, len(siltra_file.item_ids))
        self.assertEqual(
            siltra_file.item_ids.filtered(lambda i: i.process_type == "DIT").leave_id,
            leave,
        )
        self.assertEqual(leave.date_to.date(), date(2026, 1, 26))
        siltra_file_02 = self.env["hr.siltra"].create(
            {
                "name": "Test File 02",
                "file": base64.b64encode(
                    self.make_file(
                        fields.Datetime.now(),
                        [
                            {
                                "employee_id": self.employee_01,
                                "type": "DIT",
                                "date": date(2025, 12, 29),
                                "end_date": date(2026, 1, 30),
                            },
                        ],
                    )
                ),
            }
        )
        siltra_file_02.process()
        self.assertEqual(siltra_file.state, "validated")
        self.assertEqual(len(siltra_file_02.item_ids), 1)
        self.assertEqual(siltra_file_02.item_ids.process_type, "DIT")
        self.assertEqual(siltra_file_02.item_ids.leave_id, leave)
        self.assertEqual(leave.date_to.date(), date(2026, 1, 30))

    def test_DIP(self):
        siltra_file = self.env["hr.siltra"].create(
            {
                "name": "Test File",
                "file": base64.b64encode(
                    self.make_file(
                        fields.Datetime.now(),
                        [
                            {
                                "employee_id": self.employee_01,
                                "type": "DIP",
                                "date": date(2025, 12, 29),
                            },
                        ],
                    )
                ),
            }
        )
        siltra_file.process()
        self.assertEqual(siltra_file.nac_items, 0)
        self.assertEqual(siltra_file.dit_items, 0)
        self.assertEqual(siltra_file.dip_items, 1)
        self.assertEqual(siltra_file.jub_items, 0)
        self.assertEqual(len(siltra_file.item_ids), 1)
        self.assertEqual(siltra_file.item_ids.process_type, "DIP")
        self.assertFalse(siltra_file.item_ids.leave_id)
        self.assertEqual(siltra_file.state, "processed")

    def test_JUB(self):
        siltra_file = self.env["hr.siltra"].create(
            {
                "name": "Test File",
                "file": base64.b64encode(
                    self.make_file(
                        fields.Datetime.now(),
                        [
                            {
                                "employee_id": self.employee_01,
                                "type": "JUB",
                                "date": date(2025, 12, 29),
                            },
                        ],
                    )
                ),
            }
        )
        siltra_file.process()
        self.assertEqual(siltra_file.nac_items, 0)
        self.assertEqual(siltra_file.dit_items, 0)
        self.assertEqual(siltra_file.dip_items, 0)
        self.assertEqual(siltra_file.jub_items, 1)
        self.assertEqual(len(siltra_file.item_ids), 1)
        self.assertEqual(siltra_file.item_ids.process_type, "JUB")
        self.assertFalse(siltra_file.item_ids.leave_id)
        self.assertEqual(siltra_file.state, "processed")

    def test_changing_other_leaves_approved(self):
        leave_01 = self.env["hr.leave"].create(
            {
                "employee_id": self.employee_01.id,
                "holiday_status_id": self.extra_leave_type.id,
                "request_date_from": date(2025, 12, 20),
                "request_date_to": date(2025, 12, 30),
            }
        )
        leave_01.action_approve(False)
        leave_02 = self.env["hr.leave"].create(
            {
                "employee_id": self.employee_02.id,
                "holiday_status_id": self.extra_leave_type.id,
                "request_date_from": date(2025, 12, 20),
                "request_date_to": date(2026, 2, 20),
            }
        )
        leave_02.action_approve(False)
        leave_03 = self.env["hr.leave"].create(
            {
                "employee_id": self.employee_03.id,
                "holiday_status_id": self.extra_leave_type.id,
                "request_date_from": date(2026, 1, 20),
                "request_date_to": date(2026, 2, 28),
            }
        )
        leave_03.action_approve(False)
        leave_04 = self.env["hr.leave"].create(
            {
                "employee_id": self.employee_04.id,
                "holiday_status_id": self.extra_leave_type.id,
                "request_date_from": date(2026, 1, 1),
                "request_date_to": date(2026, 1, 15),
            }
        )
        leave_04.action_approve(False)

        self.assertEqual(leave_01.state, "validate")
        self.assertEqual(leave_02.state, "validate")
        self.assertEqual(leave_03.state, "validate")
        self.assertEqual(leave_04.state, "validate")
        siltra_file = self.env["hr.siltra"].create(
            {
                "name": "Test File",
                "file": base64.b64encode(
                    self.make_file(
                        fields.Datetime.now(),
                        [
                            {
                                "employee_id": self.employee_01,
                                "type": "DIT",
                                "date": date(2025, 12, 29),
                                "end_date": date(2026, 1, 26),
                            },
                            {
                                "employee_id": self.employee_02,
                                "type": "DIT",
                                "date": date(2025, 12, 29),
                                "end_date": date(2026, 1, 26),
                            },
                            {
                                "employee_id": self.employee_03,
                                "type": "DIT",
                                "date": date(2025, 12, 29),
                                "end_date": date(2026, 1, 26),
                            },
                            {
                                "employee_id": self.employee_04,
                                "type": "DIT",
                                "date": date(2025, 12, 29),
                                "end_date": date(2026, 1, 26),
                            },
                        ],
                    )
                ),
            }
        )
        siltra_file.process()
        self.assertEqual(siltra_file.nac_items, 0)
        self.assertEqual(siltra_file.dit_items, 4)
        self.assertEqual(siltra_file.dip_items, 0)
        self.assertEqual(siltra_file.jub_items, 0)
        leave_01.invalidate_recordset()
        leave_02.invalidate_recordset()
        leave_03.invalidate_recordset()
        leave_04.invalidate_recordset()
        self.assertTrue(
            self.env["hr.leave"].search(
                [
                    ("employee_id", "in", [self.employee_01.id]),
                    ("request_date_from", "=", date(2025, 12, 20)),
                    ("state", "=", "validate"),
                ]
            )
        )
        self.assertTrue(
            self.env["hr.leave"].search(
                [
                    ("employee_id", "in", [self.employee_02.id]),
                    ("request_date_from", "=", date(2025, 12, 20)),
                    ("state", "=", "validate"),
                ]
            )
        )
        self.assertTrue(
            self.env["hr.leave"].search(
                [
                    ("employee_id", "in", [self.employee_02.id]),
                    ("request_date_from", "=", date(2026, 1, 27)),
                    ("state", "=", "validate"),
                ]
            )
        )
        self.assertTrue(
            self.env["hr.leave"].search(
                [
                    ("employee_id", "in", [self.employee_03.id]),
                    ("request_date_from", "=", date(2026, 1, 27)),
                    ("state", "=", "validate"),
                ]
            )
        )
        self.assertEqual(leave_01.state, "refuse")
        self.assertEqual(leave_02.state, "refuse")
        self.assertEqual(leave_03.state, "refuse")
        self.assertEqual(leave_04.state, "refuse")
