# Copyright 2023 Dixmit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    param = (
        env["ir.config_parameter"].sudo().get_param("facturae.face.ws", default=False)
    )
    if param and param == "https://webservice.face.gob.es/facturasspp2?wsdl":
        env["ir.config_parameter"].sudo().set_param(
            "facturae.face.ws_rest", "https://se-api-face.redsara.es"
        )
    elif param:
        env["ir.config_parameter"].sudo().set_param(
            "facturae.face.ws_rest", "https://api.face.gob.es"
        )
    # We want to remove the old parameter to know in migrations in other versions
    # if the migration has been done or not, to avoid confusion
    env["ir.config_parameter"].sudo().set_param("facturae.face.ws", False)
