# © 2017 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0
from odoo.tests.common import TransactionCase


class TestL10nEsAeatExportConfig(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_onchange_export_config_line(self):
        export_config_line_env = self.env["aeat.model.export.config.line"]
        export_line_float = export_config_line_env.new()
        export_line_float.export_type = "float"
        self.assertEqual(
            export_line_float.alignment,
            "right",
            "Export type float must be aligned to the right",
        )
        export_line_str = export_config_line_env.new()
        export_line_str.export_type = "string"
        self.assertEqual(
            export_line_str.alignment,
            "left",
            "Export type string must be aligned to the left",
        )
        export_line_subtype = export_config_line_env.new()
        export_line_subtype.alignment = "left"
        export_line_subtype.decimal_size = 10
        export_line_subtype.apply_sign = True
        export_line_subtype.subconfig_id = export_line_str.id
        self.assertFalse(
            export_line_subtype.alignment, "Alignment must be False for a subtype line"
        )
        self.assertEqual(export_line_subtype.decimal_size, 0)
        self.assertFalse(
            export_line_subtype.apply_sign,
            "Apply sign must be False for a subtype line",
        )

    def test_export_config_file(self):
        export_subconfig = self.env["aeat.model.export.config"].create(
            {
                "name": "Test Export Sub Config",
                "model_number": "000",
                "config_line_ids": [
                    (
                        0,
                        0,
                        {
                            "sequence": 1,
                            "name": "<T",
                            "fixed_value": "<T",
                            "export_type": "string",
                            "size": 3,
                            "alignment": "left",
                        },
                    )
                ],
            }
        )
        export_config = self.env["aeat.model.export.config"].create(
            {
                "name": "Test Export Config",
                "model_number": "000",
                "config_line_ids": [
                    (
                        0,
                        0,
                        {
                            "sequence": 1,
                            "name": "<T",
                            "fixed_value": "<T",
                            "export_type": "string",
                            "size": 3,
                            "alignment": "left",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 2,
                            "name": "Empty spaces",
                            "fixed_value": "",
                            "export_type": "string",
                            "size": 10,
                            "alignment": "left",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 3,
                            "name": "Integer Value",
                            "fixed_value": 1,
                            "export_type": "integer",
                            "size": 3,
                            "alignment": "right",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 4,
                            "name": "Float Value",
                            "fixed_value": 15.0,
                            "export_type": "float",
                            "size": 6,
                            "decimal_size": 2,
                            "alignment": "right",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 5,
                            "name": "Boolean True Value",
                            "expression": True,
                            "export_type": "boolean",
                            "size": 2,
                            "alignment": "left",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 6,
                            "name": "Boolean False Value",
                            "expression": False,
                            "export_type": "boolean",
                            "size": 2,
                            "alignment": "left",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 7,
                            "name": ">",
                            "fixed_value": ">",
                            "size": 1,
                            "alignment": "left",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "sequence": 8,
                            "name": "False expression",
                            "export_type": "subconfig",
                            "alignment": "left",
                            "subconfig_id": export_subconfig.id,
                            "conditional_expression": "False",
                        },
                    ),
                ],
            }
        )
        new_report = self.env["l10n.es.aeat.report"].new({"name": "Test Report"})
        export_to_boe = self.env["l10n.es.aeat.report.export_to_boe"].create(
            {"name": "test_export_to_boe.txt"}
        )
        export_file = export_to_boe._export_config(new_report, export_config)
        self.assertEqual(b"<T           001001500X >", export_file)
