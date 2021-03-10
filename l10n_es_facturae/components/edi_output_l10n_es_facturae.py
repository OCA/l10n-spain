# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class EdiOutputL10nEsFacturae(Component):
    _name = "edi.output.generate.l10n_es_facturae"
    _inherit = "edi.component.output.mixin"
    _usage = "output.generate"
    _backend_type = "l10n_es_facturae"

    def generate(self):
        return self.exchange_record.record.get_facturae(True)[0]
