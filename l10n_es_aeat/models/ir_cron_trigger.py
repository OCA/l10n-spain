# Copyright 2025 Sygel - Manuel Regidor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class IrCronTrigger(models.Model):
    _inherit = "ir.cron.trigger"

    def _get_aeat_time_field(self):
        self.ensure_one()
        return False

    def _get_aeat_account_moves(self):
        self.ensure_one()
        return self.env["account.move"]

    def _get_aeat_sending_time(self, account_move):
        return False

    def aeat_do_now(self):
        for trigger in self:
            time_field = trigger._get_aeat_time_field()
            account_moves = trigger._get_aeat_account_moves()
            if time_field and account_moves:
                account_moves.write({time_field: fields.Datetime.now()})
                trigger.sudo().write({"call_at": fields.Datetime.now()})

    def aeat_cancel_now(self):
        for trigger in self:
            time_field = trigger._get_aeat_time_field()
            account_moves = trigger._get_aeat_account_moves()
            if time_field and account_moves:
                account_moves.write({time_field: False})
                trigger.sudo().unlink()

    def aeat_reschedule_sudo(self):
        for trigger in self:
            time_field = trigger._get_aeat_time_field()
            account_moves = trigger._get_aeat_account_moves()
            if time_field and account_moves:
                for account_move in account_moves:
                    sending_time = trigger._get_aeat_sending_time(account_move)
                    account_move.write({time_field: sending_time})
                    trigger.write({"call_at": sending_time})
