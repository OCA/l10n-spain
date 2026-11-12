# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import http

from odoo.addons.mail.controllers.mail import MailController


class Mod415Controller(http.Controller):
    """Answer of a partner to the 415 data sent by email: the links of the
    email are signed for these routes and for the 415 partner records."""

    def _mod415_answer(self, res_id, token, action):
        comparison, record, _redirect = (
            MailController._check_token_and_record_or_redirect(
                "l10n.es.atc.mod415.partner_record", int(res_id), token
            )
        )
        if comparison and record:
            try:
                getattr(record.sudo(), action)()
            except Exception:  # noqa: BLE001
                return http.request.render("l10n_es_atc_mod415.communication_failed")
        return http.request.render("l10n_es_atc_mod415.communication_success")

    @http.route(
        "/mod415/accept", type="http", auth="public", methods=["GET"], website=True
    )
    def mod415_accept(self, res_id, token, **kwargs):
        return self._mod415_answer(res_id, token, "action_confirm")

    @http.route(
        "/mod415/reject", type="http", auth="public", methods=["GET"], website=True
    )
    def mod415_reject(self, res_id, token, **kwargs):
        return self._mod415_answer(res_id, token, "action_exception")
