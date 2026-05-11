# Copyright 2021 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from lxml import etree

from odoo import api, models
from odoo.tools import cleanup_xml_node


class ReportFacturae(models.AbstractModel):
    """As the name is report.{module}.{template}, this model is used as
    a base to generate the unsigned facturae XML.
    """

    _name = "report.l10n_es_facturae.template_facturae"
    _inherit = "report.report_xml.abstract"
    _description = "Account Move Facturae Template without signature"

    def _get_report_values(self, docids, data=None):
        result = super()._get_report_values(docids, data=data)
        result["docs"] = self.env["account.move"].browse(docids)
        return result

    @api.model
    def generate_report(self, ir_report, docids, data=None):
        xml_facturae, content_type = super().generate_report(
            ir_report, docids, data=data
        )
        # Quitamos espacios en blanco, para asegurar que el XML final quede
        # totalmente libre de ellos.
        tree = cleanup_xml_node(xml_facturae)
        xml_facturae = etree.tostring(tree, xml_declaration=True, encoding="UTF-8")
        return xml_facturae, content_type
