# Copyright 2016 Soluntec Proyectos y Soluciones TIC. - Rubén Francés
# Copyright 2016 Soluntec Proyectos y Soluciones TIC. - Nacho Torró
# Copyright 2015 Tecnativa - Pedro M. Baeza
# Copyright 2019 César Fernández Domínguez
# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models

from .confirming_sabadell import ConfirmingSabadell


class AccountPaymentOrder(models.Model):
    _inherit = "account.payment.order"

    def generate_payment_file(self):
        self.ensure_one()
        if self.payment_method_id.code != "conf_sabadell":
            return super().generate_payment_file()
        # Sabadell payment file
        confirming_sabadell = ConfirmingSabadell(self)
        return confirming_sabadell.create_file()
