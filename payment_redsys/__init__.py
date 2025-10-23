# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

from . import models
from . import controllers

from odoo.addons.payment import reset_payment_provider, setup_provider


def post_init_hook(env):
    setup_provider(env, "redsys")


def uninstall_hook(env):
    reset_payment_provider(env, "redsys")
