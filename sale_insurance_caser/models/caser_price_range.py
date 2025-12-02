# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import re

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class CaserPriceRange(models.Model):
    _name = "caser.price.range"
    _inherit = ["caser.api.mixin"]
    _description = "Caser Insurance Price Range"
    _order = "caser_asset_type, min_price"

    caser_asset_type = fields.Selection(
        selection=[
            ("200021", "Teléfono Móvil"),
            ("262", "Tablet"),
        ],
        string="Asset Type",
        required=True,
        default="200021",
    )
    min_price = fields.Float(
        string="Minimum Price",
        required=True,
        digits="Product Price",
    )
    max_price = fields.Float(
        string="Maximum Price",
        required=True,
        digits="Product Price",
    )
    code = fields.Char(
        required=True,
        help="Code sent to Caser API for this price range",
    )
    insurance_price = fields.Float(
        digits="Product Price",
        help="Insurance price from Caser tarification (PRIMA_itotre - with taxes)",
    )
    insurance_price_notax = fields.Float(
        string="Insurance Price (No Tax)",
        digits="Product Price",
        help="Insurance price from Caser tarification (PRIMA_ipriom - without taxes)",
    )
    last_tarification_date = fields.Datetime(
        string="Last Tarification",
        readonly=True,
        help="Last time tarification was requested from Caser",
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Insurance Product",
        help="Product automatically created/updated with tarification price",
    )

    @api.constrains("min_price", "max_price")
    def _check_price_range(self):
        for record in self:
            if record.min_price >= record.max_price:
                raise ValidationError(
                    self.env._("Minimum price must be less than maximum price")
                )

    @api.model
    def get_insurance_product_for_price(self, price, asset_type=None):
        if not price:
            return self.env["product.product"]
        domain = [("min_price", "<=", price), ("max_price", ">=", price)]
        if asset_type:
            domain.append(("caser_asset_type", "=", asset_type))
        price_range = self.search(domain, limit=1)
        return price_range.product_id if price_range else self.env["product.product"]

    @api.model
    def get_code_for_amount(self, amount, asset_type=None):
        domain = [("min_price", "<=", amount), ("max_price", ">=", amount)]
        if asset_type:
            domain.append(("caser_asset_type", "=", asset_type))
        price_range = self.search(domain, limit=1)
        if not price_range:
            raise ValidationError(self.env._("No price range configured for amount"))
        return price_range.code

    def action_get_tarification_prices(self):
        for record in self:
            record._fetch_tarification_price()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": self.env._("Tarification Complete"),
                "message": self.env._(
                    "Insurance prices updated from Caser and products created/updated"
                ),
                "type": "success",
            },
        }

    def _fetch_tarification_price(self):
        # Fetch tarification price for this price range
        self.ensure_one()
        # Use middle price of the range for tarification
        test_price = (self.min_price + self.max_price) / 2
        xml_content = self._prepare_tarification_xml(test_price)
        soap_envelope = self._wrap_in_soap_envelope(xml_content)
        endpoint = self._get_caser_endpoint()
        try:
            response = self._send_caser_soap_request(endpoint, soap_envelope)
            if response.status_code == 200:
                result = self._parse_tarification_response(response.text)
                # Create or update insurance product with price INCLUDING taxes
                product = self._create_or_update_insurance_product(
                    result["price_with_tax"]
                )
                self.write(
                    {
                        "insurance_price": result["price_with_tax"],
                        "insurance_price_notax": result["price_no_tax"],
                        "last_tarification_date": fields.Datetime.now(),
                        "product_id": product.id,
                    }
                )
            else:
                raise UserError(
                    self.env._("Caser API error (HTTP %s): %s")
                    % (response.status_code, response.text)
                )
        except Exception as e:
            raise UserError(
                self.env._("Error fetching tarification for range %s: %s")
                % (self.code, str(e))
            ) from e

    _PROTOCOL_BY_ASSET_TYPE = {"200021": "61680", "262": "61681"}
    _TARIF_BRAND_CODE_BY_ASSET_TYPE = {"200021": "479", "262": "396"}

    def _prepare_tarification_xml(self, price):
        # Prepare XML for tarification request (P_COPER=00)
        self.ensure_one()
        config_params = self._get_caser_config_params()
        agency_code = config_params["agency_code"]
        asset_type = self.caser_asset_type or "200021"
        protocol = self._PROTOCOL_BY_ASSET_TYPE[asset_type]
        tarif_brand_code = self._TARIF_BRAND_CODE_BY_ASSET_TYPE[asset_type]
        schema_url = self._get_caser_schema_url()
        effective_date, expiration_date = self._get_caser_policy_dates()
        effective_str = effective_date.strftime("%Y%m%d")
        expiration_str = expiration_date.strftime("%Y%m%d")
        return f"""<SERVICIO
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xsi:schemaLocation="{schema_url}
            0301000/2419/TARIFICACION/TARIFICACION_entrada.xsd"
    idioma="CAS"
>
    <P_COPER>00</P_COPER>
    <P_NSPARAME>{protocol}</P_NSPARAME>
    <P_CAGENCIA>{agency_code}</P_CAGENCIA>
    <P_CAGENTE>000</P_CAGENTE>
    <P_FEFECTO>{effective_str}</P_FEFECTO>
    <P_CFRACCI>0</P_CFRACCI>
    <P_CIDIOMA>0</P_CIDIOMA>
    <P_NPRODUC>2419</P_NPRODUC>
    <P_COBJASE>BICO</P_COBJASE>
    <P_CSUBOBJ>ELDO</P_CSUBOBJ>
    <P_FVENCTO>{expiration_str}</P_FVENCTO>
    <TXM_ELDO_PR_3827>{price}</TXM_ELDO_PR_3827>
    <TXT_ELDO_PR_3828>Test Product</TXT_ELDO_PR_3828>
    <TXT_ELDO_PR_3829>{effective_str}</TXT_ELDO_PR_3829>
    <CBO_ELDO_PR_3825>{self.code}</CBO_ELDO_PR_3825>
    <P_CDATO1>{asset_type}</P_CDATO1>
    <P_CDATO2>{tarif_brand_code}</P_CDATO2>
    <P_CDATO3>000000000000000</P_CDATO3>
    <TXM_ELDO_CAP_3827>{price}</TXM_ELDO_CAP_3827>
    <P_LISTACOBERTURAS_LISTABEANS>
        <REPETIDO>
            <scobert>1701</scobert>
            <fefecto>{effective_str}</fefecto>
            <fvencim>{expiration_str}</fvencim>
        </REPETIDO>
        <REPETIDO>
            <scobert>1703</scobert>
            <fefecto>{effective_str}</fefecto>
            <fvencim>{expiration_str}</fvencim>
        </REPETIDO>
    </P_LISTACOBERTURAS_LISTABEANS>
    <P_CEMPRES>0001</P_CEMPRES>
</SERVICIO>"""

    def _parse_tarification_response(self, response_xml):
        # Extract P_TEXTO to check if OK
        if "<P_TEXTO>OK</P_TEXTO>" not in response_xml:
            if "<P_TEXTO>" in response_xml:
                start = response_xml.find("<P_TEXTO>") + len("<P_TEXTO>")
                end = response_xml.find("</P_TEXTO>")
                error_msg = response_xml[start:end].strip()
            else:
                error_msg = "Unknown error"
            raise UserError(self.env._("Caser tarification error: %s") % error_msg)
        result = {"price_no_tax": 0.0, "price_with_tax": 0.0}
        prima_ipriom_matches = re.findall(
            r"<PRIMA_ipriom>([\d.]+)</PRIMA_ipriom>", response_xml
        )
        prima_itotre_matches = re.findall(
            r"<PRIMA_itotre>([\d.]+)</PRIMA_itotre>", response_xml
        )
        if len(prima_ipriom_matches) >= 3:
            result["price_no_tax"] = float(prima_ipriom_matches[2])
        if len(prima_itotre_matches) >= 3:
            result["price_with_tax"] = float(prima_itotre_matches[2])
        return result

    def _create_or_update_insurance_product(self, price):
        # Create or update insurance product for this price range.
        self.ensure_one()
        product_name = self.env._("Seguro Caser")
        default_code = f"CASER_RANGE_{self.caser_asset_type}_{self.code}"
        product = self.env["product.product"].search(
            [
                ("default_code", "=", default_code),
            ],
            limit=1,
        )
        tax = self.env["account.tax"].search(
            [("name", "=", "IVA 0% SUPLIDOS"), ("type_tax_use", "=", "sale")],
            limit=1,
        )
        vals = {
            "name": product_name,
            "default_code": default_code,
            "type": "service",
            "list_price": price,
            "standard_price": price,
            "categ_id": self.env.ref("product.product_category_all").id,
            "sale_ok": True,
            "purchase_ok": False,
            "taxes_id": [(6, 0, tax.ids)],
        }
        if product:
            product.write(vals)
        else:
            product = self.env["product.product"].create(vals)
        return product
