# Copyright 2022 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    backend = env.ref("l10n_es_facturae_face.face_backend")
    if "webservice_backend_id" in backend._fields:
        backend.write({"webservice_backend_id": False})
    webservice = env.ref(
        "l10n_es_facturae_face.face_webservice", raise_if_not_found=False
    )
    if not webservice:
        return
    # As it was FACe, this was a problem. We need to change it....
    webservice.write({"protocol": "http"})
    env["ir.config_parameter"].sudo().set_param("facturae.face.ws", webservice.url)
    webservice.unlink()
