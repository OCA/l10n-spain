from . import controllers
from . import models

from odoo.addons.payment import setup_provider, reset_payment_provider


def post_init_hook(cr, registry):
    setup_provider(cr, registry, "sequra")


def uninstall_hook(cr, registry):
    reset_payment_provider(cr, registry, "sequra")
