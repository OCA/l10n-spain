###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .viaxpress_request import init_request


class ResCompany(models.Model):
    _inherit = "res.company"

    viaxpress_client_id = fields.Char(
        string="Client ID",
        help="Client ID for the VIAXPRESS API",
    )
    viaxpress_user = fields.Char(
        string="User",
        help="User for the ViaXpress API",
    )
    viaxpress_password = fields.Char(
        string="Password",
        help="Password for the ViaXpress API",
    )

    viaxpress_host = fields.Char(
        string="Host",
        help="Host for the ViaXpress API",
    )
    viaxpress_port = fields.Char(
        string="Port",
        help="Port for the ViaXpress API",
    )
    viaxpress_url = fields.Char(
        string="URL",
        help="URL for the ViaXpress API",
        compute="_compute_viaxpress_config",
        store=True,
    )
    viaxpress_wsdl_url = fields.Char(
        string="WSDL URL",
        help="WSDL URL for the ViaXpress API",
        compute="_compute_viaxpress_config",
        store=True,
    )

    viaxpress_intraday = fields.Boolean(
        string="Allows Intraday",
        readonly=True,
        help="This company allows intraday shipments",
    )

    viaxpress_last_sync = fields.Datetime(
        string="Last Sync",
        readonly=True,
        help="Last time this company was synced with ViaXpress",
    )

    @api.depends("viaxpress_host", "viaxpress_port")
    def _compute_viaxpress_config(self):
        for record in self:
            url, wsdl_url = (False, False)

            if record.viaxpress_host and record.viaxpress_port:
                url = "http://" + record.viaxpress_host + ":" + record.viaxpress_port
                wsdl_url = url + "/ServicioVxClientes.asmx?WSDL"

            record.viaxpress_url = url
            record.viaxpress_wsdl_url = wsdl_url

    def _prepare_viaxpress_client(self):
        request_data = {
            "GetDatosCliente": {
                "IdCliente": self.viaxpress_client_id,
                "Usuario": self.viaxpress_user,
                "Password": self.viaxpress_password,
            },
        }

        return request_data

    def _set_viaxpress_data(self):
        request = init_request(self)
        client_request = self._prepare_viaxpress_client()
        client_data = request._get_client_data(client_request)

        self.viaxpress_intraday = client_data["allow_intraday"]

    def sync_with_viaxpress(self):
        needed_fields = [
            "viaxpress_client_id",
            "viaxpress_user",
            "viaxpress_password",
            "viaxpress_host",
            "viaxpress_port",
        ]

        for field in needed_fields:
            if not getattr(self, field):
                raise UserError(
                    _("Field '%s' is required") % self._fields[field].string
                )

        self._set_viaxpress_data()
        self.viaxpress_last_sync = fields.Datetime.now()
