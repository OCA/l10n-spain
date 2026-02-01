# © 2015 Antiun Ingenieria S.L. - Antonio Espinosa
# © 2015 Antiun Ingenieria S.L. - Jairo Llopis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Define Spanish specific configuration in res.country."""
    spain = env.ref("base.es")
    _logger.info("Setting Spain NUTS configuration")
    spain.write(
        {
            "state_level": 4,
        }
    )
