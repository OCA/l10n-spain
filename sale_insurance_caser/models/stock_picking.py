# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import re

from odoo import models
from odoo.exceptions import UserError
from odoo.tools import config


class StockPicking(models.Model):
    _name = "stock.picking"
    _inherit = ["stock.picking", "caser.api.mixin"]

    def _action_done(self):
        res = super()._action_done()
        for picking in self:
            picking._assign_caser_insured_lots()
            insurance_lines = picking._get_insurance_lines_with_lots()
            for insurance_line in insurance_lines:
                picking.with_delay(
                    channel="root.caser",
                    description=self.env._("Caser insurance %s")
                    % insurance_line.order_id.name,
                )._send_caser_insurance_request(insurance_line)
        return res

    def _get_insurance_lines_with_lots(self):
        if not self.sale_id:
            return self.env["sale.order.line"]
        return self.sale_id.order_line.filtered(
            lambda line: line.is_caser_insurance and line.caser_lot_id
        )

    def _assign_caser_insured_lots(self):
        # Assign delivered lots to insurance lines matching the correct price range
        for picking in self:
            if not picking.sale_id:
                continue
            for sale_line in picking._get_product_lines_to_insure():
                # Get the correct insurance product for this sale line's price
                insurance_product = sale_line._get_caser_insurance_product()
                if not insurance_product:
                    continue
                # Get available insurance lines for this specific insurance product
                available_lines = picking._get_available_insurance_lines_for_product(
                    insurance_product
                )
                if not available_lines:
                    continue
                # Assign lots to the matching insurance lines
                lots_to_assign = picking._get_lots_to_assign(sale_line)
                for lot in lots_to_assign:
                    if not available_lines:
                        break
                    available_lines[0].caser_lot_id = lot.id
                    available_lines = available_lines[1:]

    def _get_available_insurance_lines_for_product(self, insurance_product):
        return self.sale_id.order_line.filtered(
            lambda line: (
                line.is_caser_insurance
                and not line.caser_lot_id
                and line.product_id == insurance_product
            )
        )

    def _get_product_lines_to_insure(self):
        return self.sale_id.order_line.filtered(
            lambda line: line.caser_insure_quantity > 0 and not line.is_caser_insurance
        )

    def _get_lots_to_assign(self, sale_line):
        delivered_lots = self.move_line_ids.filtered(
            lambda ml: ml.move_id.sale_line_id == sale_line and ml.lot_id
        ).mapped("lot_id")
        assigned_lots = self.sale_id.order_line.filtered(
            lambda line: line.is_caser_insurance
            and line.caser_lot_id
            and line.caser_lot_id.product_id == sale_line.product_id
        ).mapped("caser_lot_id")
        new_lots = [lot for lot in delivered_lots if lot not in assigned_lots]
        max_lots = sale_line.caser_insure_quantity - len(assigned_lots)
        return new_lots[:max_lots]

    def _send_caser_insurance_request(self, insurance_line):
        self.ensure_one()
        try:
            if not self._validate_insurance_request(insurance_line):
                return
            self._validate_caser_required_fields(insurance_line)
            endpoint = self._get_caser_endpoint()
            soap_envelope = self._prepare_soap_request(insurance_line)
            insurance_line.write(
                {
                    "caser_request_xml": soap_envelope,
                }
            )
            response = self._send_caser_soap_request(endpoint, soap_envelope)
            self._process_caser_response(insurance_line, response)
        except Exception as e:
            self._handle_request_error(insurance_line, e)
            self._caser_notify_failure(insurance_line, e)
            # Commit to preserve request/response XML and error message on the
            # insurance line even after the queue job rollback; Caser may have
            # already created the policy on their side.
            if not config["test_enable"]:
                self.env.cr.commit()  # pylint: disable=invalid-commit
            raise

    def _caser_notify_failure(self, insurance_line, error):
        if not self.sale_id:
            return
        product = insurance_line.caser_lot_id.product_id or insurance_line.product_id
        self.sale_id._caser_handle_failure(
            self.env._("Caser insurance could not be issued for %(product)s: %(error)s")
            % {"product": product.display_name, "error": str(error)}
        )

    def _validate_insurance_request(self, insurance_line):
        if not self.sale_id:
            return False
        if not insurance_line or not insurance_line.caser_lot_id:
            raise UserError(self.env._("Invalid insurance line or no lot assigned"))
        # Validate all required configuration parameters
        config = self.env["ir.config_parameter"].sudo()
        required_params = {
            "sale_insurance_caser.username": "Caser username",
            "sale_insurance_caser.agency_code": "Caser agency code",
            "sale_insurance_caser.agent_code": "Caser agent code",
            "sale_insurance_caser.sica_code": "Caser SICA code",
        }
        missing_params = []
        for param_key, param_name in required_params.items():
            if not config.get_param(param_key):
                missing_params.append(param_name)
        if missing_params:
            raise UserError(
                self.env._(
                    "Missing required Caser configuration parameters:\n- %s\n\n"
                    "Please configure them in Sales > Configuration > Settings"
                )
                % "\n- ".join(missing_params)
            )
        return True

    def _validate_brand_code_errors(self, product, asset_type):
        errors = []
        if not product.product_brand_id:
            errors.append(
                self.env._("Product '%s' must have a brand assigned")
                % product.display_name
            )
        else:
            if not product.product_brand_id._get_caser_code(asset_type):
                errors.append(
                    self.env._(
                        "Brand '%(brand)s' has no Caser code configured for asset "
                        "type %(asset_type)s"
                    )
                    % {
                        "brand": product.product_brand_id.name,
                        "asset_type": asset_type,
                    }
                )
        return errors

    def _validate_caser_required_fields(self, insurance_line):
        self.ensure_one()
        errors = []
        partner = self.sale_id.partner_id
        # Validate IDDOC (NIF/CIF) - required field
        vat = (partner.vat or "").replace("ES", "")
        if not vat or len(vat) < 9:
            errors.append(
                self.env._(
                    "Customer VAT/NIF is required and must be at least 9 characters"
                )
            )
        # Validate VIA (street) - required field
        if not partner.street:
            errors.append(self.env._("Customer street address is required"))
        # Validate POBLACION (city) - required field
        if not partner.city:
            errors.append(self.env._("Customer city is required"))
        # Validate COD_POSTAL (zip code) - required field
        if not partner.zip:
            errors.append(self.env._("Customer zip code is required"))
        # Validate PROVINCIA (state) - required field
        if not partner.state_id or not partner.state_id.code:
            errors.append(self.env._("Customer state/province is required"))
        # Validate company data for billing address
        company = self.company_id
        if not company.street:
            errors.append(self.env._("Company street address is required"))
        if not company.city:
            errors.append(self.env._("Company city is required"))
        if not company.zip:
            errors.append(self.env._("Company zip code is required"))
        if not company.state_id or not company.state_id.code:
            errors.append(self.env._("Company state/province is required"))
        # Validate product and category data
        lot = insurance_line.caser_lot_id
        if lot:
            # Validate TXM_ELDO_CAP_3827 (sale value) - required field
            amount = self._get_product_amount_and_description(insurance_line)[0]
            if not amount or amount <= 0:
                errors.append(self.env._("Product price must be greater than 0"))
            categ = lot.product_id.categ_id
            if not categ.caser_asset_type:
                errors.append(
                    self.env._(
                        "Product category '%s' must have a Caser Asset Type configured"
                    )
                    % categ.display_name
                )
            if not categ.caser_protocol:
                errors.append(
                    self.env._(
                        "Product category '%s' must have a Caser Protocol configured"
                    )
                    % categ.display_name
                )
            errors.extend(
                self._validate_brand_code_errors(lot.product_id, categ.caser_asset_type)
            )
        if errors:
            error_msg = self.env._(
                "Missing required fields to send to CASER:\n\n"
            ) + "\n".join([f"• {e}" for e in errors])
            raise UserError(error_msg)

    def _prepare_soap_request(self, insurance_line):
        xml_payload = self._prepare_caser_policy_xml(insurance_line)
        return self._wrap_in_soap_envelope(xml_payload)

    def _process_caser_response(self, insurance_line, response):
        insurance_line.write({"caser_response_xml": response.text})
        if response.status_code != 200:
            raise UserError(
                self.env._("HTTP Error %s: %s") % (response.status_code, response.text)
            )
        result = self._parse_caser_response(response.text)
        # Persist policy/price before validating so a price mismatch does not
        # wipe out the connection data Caser already committed on their side.
        insurance_line.write(
            {
                "caser_policy_number": result["policy_number"],
                "caser_insurance_price": result["insurance_price"],
            }
        )
        self._validate_caser_price(insurance_line, result["insurance_price"])

    def _handle_request_error(self, insurance_line, error):
        error_msg = self.env._("Request error: %s") % str(error)
        insurance_line.write(
            {
                "caser_error_message": error_msg,
            }
        )

    def _validate_caser_price(self, insurance_line, caser_price):
        # A price mismatch does not abort the flow: the policy is already
        # issued by Caser. Log it on the line and the order for review.
        self.ensure_one()
        line_price = insurance_line.price_unit
        if abs(line_price - caser_price) > 0.01:
            msg = self.env._(
                "Price mismatch: line price %(line)s but Caser returned %(caser)s"
            ) % {"line": line_price, "caser": caser_price}
            insurance_line.caser_error_message = msg
            self.sale_id._caser_handle_failure(msg)

    def _parse_caser_response(self, response_xml):
        # Extract P_TEXTO value if present
        error_message = ""
        if "<P_TEXTO>" in response_xml:
            start = response_xml.find("<P_TEXTO>") + len("<P_TEXTO>")
            end = response_xml.find("</P_TEXTO>")
            texto_value = response_xml[start:end].strip()
            if texto_value != "OK":
                error_message = texto_value
        # Raise error if P_DONDE=NOK or P_TEXTO is not OK
        if "<P_DONDE>NOK</P_DONDE>" in response_xml or error_message:
            normas = re.findall(r"<tprolin>(.*?)</tprolin>", response_xml)
            raise UserError(
                self.env._("Caser API Error: %s")
                % (" | ".join(normas) if normas else error_message or "Unknown error")
            )
        result = {"policy_number": "", "insurance_price": 0.0}
        # Extract policy number
        if "<P_NPOLPRO>" in response_xml:
            start = response_xml.find("<P_NPOLPRO>") + len("<P_NPOLPRO>")
            end = response_xml.find("</P_NPOLPRO>")
            result["policy_number"] = response_xml[start:end].strip()
        # Extract insurance price (PRIMA_itotre - Prima Total)
        if "<PRIMA_itotre>" in response_xml:
            start = response_xml.find("<PRIMA_itotre>") + len("<PRIMA_itotre>")
            end = response_xml.find("</PRIMA_itotre>")
            price_str = response_xml[start:end].strip()
            try:
                result["insurance_price"] = float(price_str)
            except (ValueError, TypeError):
                result["insurance_price"] = 0.0
        return result

    def _prepare_caser_policy_xml(self, insurance_line):
        self.ensure_one()
        vals = self._prepare_caser_policy_vals(insurance_line)
        schema_url = self._get_caser_schema_url()
        xml_payload = f"""<SERVICIO
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xsi:schemaLocation="{schema_url}
            0301000/2419/CONTRATACION/CONTRATACION_entrada.xsd"
    idioma="CAS"
>
    <P_COPER>03</P_COPER>
    <P_NSPARAME>{vals['protocol']}</P_NSPARAME>
    <P_CAGENCIA>{vals['agency_code']}</P_CAGENCIA>
    <P_CAGENTE>000</P_CAGENTE>
    <P_CFRACCI>0</P_CFRACCI>
    <P_CIDIOMA>0</P_CIDIOMA>
    <P_FEFECTO>{vals['effective_date']}</P_FEFECTO>
    <P_NPRODUC>2419</P_NPRODUC>
    <P_COBJASE>BICO</P_COBJASE>
    <P_CSUBOBJ>ELDO</P_CSUBOBJ>
    <P_FVENCTO>{vals['expiration_date']}</P_FVENCTO>
    <TXM_ELDO_PR_3827>{vals['amount']}</TXM_ELDO_PR_3827>
    <TXT_ELDO_PR_3828>{vals['brand']}</TXT_ELDO_PR_3828>
    <TXT_ELDO_PR_3829>{vals['effective_date']}</TXT_ELDO_PR_3829>
    <CBO_ELDO_PR_3825>{vals['price_range_code']}</CBO_ELDO_PR_3825>
    <P_CDATO1>{vals['asset_type']}</P_CDATO1>
    <P_CDATO2>{vals['brand_code']}</P_CDATO2>
    <P_CDATO3>{vals['serial_number']}</P_CDATO3>
    <TXM_ELDO_CAP_3827>{vals['amount']}</TXM_ELDO_CAP_3827>
    <P_LISTACOBERTURAS_LISTABEANS>
        <REPETIDO><scobert>1701</scobert></REPETIDO>
        <REPETIDO><scobert>1703</scobert></REPETIDO>
    </P_LISTACOBERTURAS_LISTABEANS>
    <P_CEMPRES>0001</P_CEMPRES>
    <CTPDOC>{vals['id_type']}</CTPDOC>
    <IDDOC>{vals['nif']}</IDDOC>
    <L_IDDOC>{vals['nif_letter']}</L_IDDOC>
    <NOM>{vals['first_name']} </NOM>
    <APELL_1>{vals['last_name1']}</APELL_1>
    <APELL_2>{vals['last_name2']}</APELL_2>
    <VIA>{vals['street']}</VIA>
    <RESTO_DOM></RESTO_DOM>
    <TIPO_VIA>{vals['street_type']}</TIPO_VIA>
    <POBLACION>{vals['city']} </POBLACION>
    <COD_POSTAL>{vals['zip']}</COD_POSTAL>
    <PROVINCIA>{vals['state_code']}</PROVINCIA>
    <NUM>{vals['phone']}</NUM>
    <ASEG_TIPO_VIA>   </ASEG_TIPO_VIA>
    <ASEG_RESTO_DOM></ASEG_RESTO_DOM>
    <ASEG_CTPDOC>{vals['id_type']}</ASEG_CTPDOC>
    <ASEG_IDDOC>{vals['nif']}</ASEG_IDDOC>
    <ASEG_L_IDDOC>{vals['nif_letter']}</ASEG_L_IDDOC>
    <ASEG_NOM>{vals['first_name']} </ASEG_NOM>
    <ASEG_APELL_1>{vals['last_name1']}</ASEG_APELL_1>
    <ASEG_APELL_2>{vals['last_name2']}</ASEG_APELL_2>
    <ASEG_VIA>{vals['street']}</ASEG_VIA>
    <ASEG_POBLACION>{vals['city']} </ASEG_POBLACION>
    <ASEG_COD_POSTAL>{vals['zip']}</ASEG_COD_POSTAL>
    <ASEG_PROVINCIA>{vals['state_code']}</ASEG_PROVINCIA>
    <ASEG_NUM>{vals['phone']}</ASEG_NUM>
    <TIPO_VIAC>{vals['street_type']}</TIPO_VIAC>
    <VIAC>{vals['company_street']}</VIAC>
    <RESTO_DOMC></RESTO_DOMC>
    <POBLACIONC>{vals['company_city']}</POBLACIONC>
    <COD_POSTALC>{vals['company_zip']}</COD_POSTALC>
    <PROVINCIAC>{vals['company_state_code']}</PROVINCIAC>
    <P_EMITIR>S</P_EMITIR>
    <P_CTIPOPAGO>1</P_CTIPOPAGO>
    <PAGO_COMBINADO>N</PAGO_COMBINADO>
    <P_CEMPRES>0001</P_CEMPRES>
    <P_AGENTE>{vals['agent_code']}</P_AGENTE>
    <P_USUARIO_WEB>{vals['web_username']}</P_USUARIO_WEB>
    <P_CSBC>{vals['sica_code']}</P_CSBC>
    <COEL>{vals['email']}</COEL>
    <USCO>9999</USCO>
    <TELM>{vals['phone']}</TELM>
    <USTM>9999</USTM>
    <DATOSCONTACTO_POR_POLIZA>S</DATOSCONTACTO_POR_POLIZA>
</SERVICIO>"""
        return xml_payload

    def _get_brand_code(self, product, asset_type):
        brand = product.product_brand_id
        if not brand:
            raise UserError(
                self.env._("Product '%s' must have a brand assigned")
                % product.display_name
            )
        code = brand._get_caser_code(asset_type)
        if not code:
            raise UserError(
                self.env._(
                    "Brand '%(brand)s' has no Caser code configured for asset type "
                    "%(asset_type)s. Please set it in the brand's form."
                )
                % {"brand": brand.name, "asset_type": asset_type}
            )
        return code

    def _prepare_caser_policy_vals(self, insurance_line):
        self.ensure_one()
        lot = insurance_line.caser_lot_id
        if not lot:
            raise UserError(self.env._("Insurance line must have an assigned lot"))
        amount, product_desc = self._get_product_amount_and_description(insurance_line)
        effective_date, expiration_date = self._get_caser_policy_dates()
        partner_data = self._get_partner_data()
        company_data = self._get_company_data()
        # Get asset type and protocol from product category
        categ = lot.product_id.categ_id
        if not categ.caser_asset_type:
            raise UserError(
                self.env._(
                    "Product category '%s' must have a Caser Asset Type configured"
                )
                % categ.display_name
            )
        if not categ.caser_protocol:
            raise UserError(
                self.env._(
                    "Product category '%s' must have a Caser Protocol configured"
                )
                % categ.display_name
            )
        asset_type = categ.caser_asset_type
        protocol = categ.caser_protocol
        brand_code = self._get_brand_code(lot.product_id, asset_type)
        config_params = self._get_caser_config_params()
        return {
            **config_params,
            "protocol": protocol,
            "effective_date": effective_date.strftime("%Y%m%d"),
            "expiration_date": expiration_date.strftime("%Y%m%d"),
            "amount": amount,
            "price_range_code": self.env["caser.price.range"].get_code_for_amount(
                amount, asset_type
            ),
            "brand": product_desc,
            "asset_type": asset_type,
            "brand_code": brand_code,
            "serial_number": lot.name or "N/A",
            **partner_data,
            **company_data,
        }

    def _get_product_amount_and_description(self, insurance_line):
        # Get the amount and description for the insured product from the sale line
        self.ensure_one()
        lot = insurance_line.caser_lot_id
        move_line = self.move_line_ids.filtered(lambda ml: ml.lot_id == lot)
        sale_line = move_line[0].move_id.sale_line_id
        return sale_line.price_reduce_taxinc, sale_line.product_id.name

    def _get_partner_data(self):
        partner = self.sale_id.partner_id
        name_parts = (partner.name or "").split()
        vat = (partner.vat or "").replace("ES", "")
        return {
            "id_type": "1",
            "nif": vat[:8],
            "nif_letter": vat[-1] if vat else "X",
            "first_name": name_parts[0] if name_parts else "",
            "last_name1": name_parts[1]
            if len(name_parts) > 1
            else name_parts[0]
            if name_parts
            else "",
            "last_name2": name_parts[2] if len(name_parts) > 2 else "",
            "street": partner.street or "",
            "street_type": "CL",
            "city": partner.city or "",
            "zip": partner.zip or "",
            "state_code": self._get_numeric_state_code(partner.state_id.code),
            "phone": "".join(
                c for c in (partner.phone or partner.mobile or "") if c.isdigit()
            )[:9],
            "email": partner.email or "",
        }

    def _get_company_data(self):
        company = self.company_id
        return {
            "company_street": company.street or "",
            "company_city": company.city or "",
            "company_zip": company.zip or "",
            "company_state_code": self._get_numeric_state_code(company.state_id.code),
        }

    def _get_numeric_state_code(self, state_code):
        province_map = {
            "VI": "01",
            "AB": "02",
            "A": "03",
            "AL": "04",
            "AV": "05",
            "BA": "06",
            "PM": "07",
            "B": "08",
            "BU": "09",
            "CC": "10",
            "CA": "11",
            "CS": "12",
            "CR": "13",
            "CO": "14",
            "C": "15",
            "CU": "16",
            "GI": "17",
            "GR": "18",
            "GU": "19",
            "SS": "20",
            "H": "21",
            "HU": "22",
            "J": "23",
            "LE": "24",
            "L": "25",
            "LO": "26",
            "LU": "27",
            "M": "28",
            "MA": "29",
            "MU": "30",
            "NA": "31",
            "OR": "32",
            "O": "33",
            "P": "34",
            "GC": "35",
            "PO": "36",
            "SA": "37",
            "TF": "38",
            "S": "39",
            "SG": "40",
            "SE": "41",
            "SO": "42",
            "T": "43",
            "TE": "44",
            "TO": "45",
            "V": "46",
            "VA": "47",
            "BI": "48",
            "ZA": "49",
            "Z": "50",
            "CE": "51",
            "ME": "52",
        }
        return province_map.get(state_code or "", state_code or "")
