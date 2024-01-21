# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging
from lxml import etree

from odoo import _, api, models, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ReportTemplateFacturae(models.AbstractModel):
    _name = "report.l10n_es_facturae.template_facturae"
    _inherit = "report.report_xml.abstract"
    _description = "Account Move Facturae unsigned"

    def _get_report_values(self, docids, data=None):
        result = super()._get_report_values(docids, data=data)
        result["docs"] = self.env["account.move"].browse(docids)
        return result

    @api.model
    def generate_report(self, ir_report, docids, data=None):
        move = self.env["account.move"].browse(docids)
        move.ensure_one()
        move.validate_facturae_fields()
        xml_facturae, content_type = super().generate_report(
            ir_report, docids, data=data
        )
        # Quitamos espacios en blanco, para asegurar que el XML final quede
        # totalmente libre de ellos.
        tree = etree.fromstring(xml_facturae, etree.XMLParser(remove_blank_text=True))
        xml_facturae = etree.tostring(tree, xml_declaration=True, encoding="UTF-8")
        self._validate_facturae(move, xml_facturae)
        return xml_facturae, content_type

    def _get_facturae_schema_file(self, move):
        return tools.file_open(
            "addons/l10n_es_facturae/data/Facturaev%s.xsd"
            % move.get_facturae_version(),
        )

    def _validate_facturae(self, move, xml_string):
        facturae_schema = etree.XMLSchema(
            etree.parse(self._get_facturae_schema_file(move))
        )
        try:

            facturae_schema.assertValid(etree.fromstring(xml_string))
        except Exception as e:
            _logger.warning("The XML file is invalid against the XML Schema Definition")
            _logger.warning(xml_string)
            _logger.warning(e)
            raise UserError(
                _(
                    "The generated XML file is not valid against the official "
                    "XML Schema Definition. The generated XML file and the "
                    "full error have been written in the server logs. Here "
                    "is the error, which may give you an idea on the cause "
                    "of the problem : %s"
                )
                % str(e)
            ) from e
        return True
