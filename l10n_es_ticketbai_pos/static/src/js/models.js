/* Copyright 2021 Binovo IT Human Project SL
   Copyright 2022 Landoo Sistemas de Informacion SL
   Copyright 2025 Binhex
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/
odoo.define("l10n_es_ticketbai_pos.models", function (require) {
    "use strict";

    const {PosGlobalState, Order, Orderline} = require("point_of_sale.models");
    const Registries = require("point_of_sale.Registries");
    const {Gui} = require("point_of_sale.Gui");
    const tbai_models = require("l10n_es_ticketbai_pos.tbai_models");

    const core = require("web.core");
    const _t = core._t;
    const tbai = window.tbai;

    const L10nEsTicketBAIPosGlobalState = (OriginalPosGlobalState) =>
        class extends OriginalPosGlobalState {
            constructor() {
                super(...arguments);
                this.tbai_version = null;
                this.tbai_qr_base_url = null;
                this.tbai_vat_regime_keys = null;
                this.tbai_last_invoice_data = null;
            }
            async _processData(loadedData) {
                await super._processData(...arguments);
                if (this.company.tbai_enabled) {
                    const config = loadedData["pos.config"];
                    this.tbai_vat_regime_keys = loadedData.tbai_vat_regime_keys;
                    this.tbai_version = loadedData.tbai_version;
                    this.tbai_qr_base_url = loadedData.tbai_qr_base_url;
                    this.tbai_last_invoice_data = loadedData.tbai_last_invoice_data;
                    return this.env.services
                        .rpc({
                            model: "pos.config",
                            method: "get_tbai_p12_and_friendlyname",
                            args: [config.id],
                        })
                        .then((args) => {
                            return tbai.TbaiSigner.fromBuffer(
                                atob(args[0]),
                                args[1],
                                args[2]
                            ).then(
                                (signer) => {
                                    this.tbai_signer = signer;
                                },
                                (err) => {
                                    console.error(err);
                                }
                            );
                        });
                }
            }
            get_country_by_id(id) {
                return this.countries.find((country) => country.id === id) || null;
            }
            get_country_code_by_id(id) {
                const country = this.get_country_by_id(id);
                return (country && country.code.toUpperCase()) || null;
            }
            get_tbai_vat_regime_key_by_id(id) {
                return this.tbai_vat_regime_keys.find((key) => key.id === id) || null;
            }
            get_tbai_vat_regime_key_code_by_id(id) {
                const tbai_vat_regime_key = this.get_tbai_vat_regime_key_by_id(id);
                return (tbai_vat_regime_key && tbai_vat_regime_key.code) || null;
            }
            push_single_order(order) {
                if (this.company.tbai_enabled && order) {
                    return order.tbai_current_invoice.then((tbai_inv) => {
                        const tbai_last_invoice_data = {
                            order: {
                                simplified_invoice:
                                    tbai_inv.number_prefix + tbai_inv.number,
                            },
                            signature_value: tbai_inv.signature_value,
                            number: tbai_inv.number,
                            number_prefix: tbai_inv.number_prefix,
                            expedition_date: tbai_inv.expedition_date,
                        };
                        this.set_tbai_last_invoice_data(tbai_last_invoice_data);
                        return super.push_single_order(...arguments);
                    });
                }
                return super.push_single_order(...arguments);
            }
            get_tbai_last_invoice_data() {
                /**
                 * Retrieves the JSON data of the last invoice from the browser database.
                 *
                 * @constant {Object} db_json_last_invoice_data - The JSON data of the last invoice.
                 * @property {Function} this.db.get_tbai_json_last_invoice_data - Function to get the last invoice data in JSON format from the browse database.
                 */
                const db_json_last_invoice_data =
                    this.db.get_tbai_json_last_invoice_data();
                return Object.keys(db_json_last_invoice_data).length
                    ? db_json_last_invoice_data
                    : this.tbai_last_invoice_data || null;
            }
            set_tbai_last_invoice_data(data) {
                this.tbai_last_invoice_data = data;
                this.db.set_tbai_json_last_invoice_data(data);
            }
            scan_product(parsed_code) {
                if (this.company.tbai_enabled) {
                    const product = this.db.get_product_by_barcode(
                        parsed_code.base_code
                    );
                    if (!product) {
                        return false;
                    }
                    if (product.taxes_id !== 1) {
                        Gui.showPopup("Error", {
                            title: _t("TicketBAI"),
                            body: _t(
                                `Please set a tax for product ${product.display_names}.`
                            ),
                        });
                        return true;
                    }
                }
                return super.scan_product(...arguments);
            }
        };
    Registries.Model.extend(PosGlobalState, L10nEsTicketBAIPosGlobalState);

    const L10nEsTicketBAIPosOrderline = (OriginalOrderline) =>
        class extends OriginalOrderline {
            export_as_JSON() {
                const json = super.export_as_JSON(...arguments);
                if (this.pos.company.tbai_enabled) {
                    const product = this.get_product();
                    const tax = this.get_taxes()[0];
                    const fp_taxes = this.pos.get_taxes_after_fp(
                        [tax.id],
                        this.order.fiscal_position
                    );
                    json.tbai_description = product.display_name || "";
                    if (fp_taxes) {
                        json.tbai_vat_amount = tax.amount;
                        json.tbai_price_without_tax = this.get_price_without_tax();
                        json.tbai_price_with_tax = this.get_price_with_tax();
                    }
                    json.tbai_price_unit =
                        fp_taxes.length > 0
                            ? this.compute_all(
                                  fp_taxes,
                                  json.price_unit,
                                  1,
                                  this.pos.currency.rounding,
                                  true
                              ).total_excluded
                            : json.price_unit;
                }
                return json;
            }
        };
    Registries.Model.extend(Orderline, L10nEsTicketBAIPosOrderline);

    const L10nEsTicketBAIPosOrder = (OriginalOrder) =>
        class extends OriginalOrder {
            constructor() {
                super(...arguments);
                this.tbai_simplified_invoice = null;
                this.tbai_current_invoice = $.when();
                if (this.pos.company.tbai_enabled && "json" in arguments[1]) {
                    this.tbai_simplified_invoice =
                        new tbai_models.TicketBAISimplifiedInvoice(
                            {},
                            {
                                pos: this.pos,
                                tbai_identifier: arguments[1].json.tbai_identifier,
                                tbai_qr_src: arguments[1].json.tbai_qr_src,
                            }
                        );
                }
                return this;
            }
            check_products_have_taxes() {
                return this.get_orderlines().every(
                    (line) => line.get_taxes().length === 1
                );
            }
            check_company_vat() {
                return Boolean(this.pos.company.vat);
            }
            check_partner_country_code(partner) {
                return Boolean(partner && partner.country_id);
            }
            check_simplified_invoice_spanish_partner(partner) {
                if (!partner) {
                    return true;
                }
                if (!this.check_partner_country_code(partner)) {
                    return false;
                }
                const country_code = this.pos.get_country_code_by_id(
                    partner.country_id[0]
                );
                return country_code === "ES" || this.to_invoice;
            }
            check_partner_vat(partner) {
                if (!partner) return true;
                if (!this.check_partner_country_code(partner)) return false;
                const country_code = this.pos.get_country_code_by_id(
                    partner.country_id[0]
                );
                if (country_code === "ES") {
                    return Boolean(partner.vat);
                }
                return this._check_foreign_partner_vat(partner);
            }
            _check_foreign_partner_vat(partner) {
                if (partner.tbai_partner_idtype === "02") {
                    return Boolean(partner.vat);
                }
                return Boolean(partner.tbai_partner_identification_number);
            }
            check_fiscal_position_vat_regime_key() {
                return !(
                    this.fiscal_position && !this.fiscal_position.tbai_vat_regime_key
                );
            }
            check_tbai_conf() {
                return (
                    this.check_company_vat() &&
                    this.check_simplified_invoice_spanish_partner() &&
                    this.check_partner_vat() &&
                    this.check_fiscal_position_vat_regime_key() &&
                    this.check_products_have_taxes()
                );
            }
            export_as_JSON() {
                const json = super.export_as_JSON(...arguments);
                if (this.pos.company.tbai_enabled) {
                    const taxLines = [];
                    const order = this;
                    this.get_tax_details().forEach((taxDetail) => {
                        const taxLineDict = taxDetail;
                        taxLineDict.baseAmount =
                            order.get_base_by_tax()[taxDetail.tax.id];
                        taxLines.push([0, 0, taxLineDict]);
                    });
                    json.taxLines = taxLines;
                    const tbai_inv = this.tbai_simplified_invoice || null;
                    if (tbai_inv !== null) {
                        const datas = tbai_inv.datas;
                        const signature_value = tbai_inv.signature_value;
                        if (datas !== null && signature_value !== null) {
                            json.tbai_signature_value = signature_value;
                            json.tbai_datas = datas;
                            json.tbai_vat_regime_key = tbai_inv.vat_regime_key;
                            json.tbai_identifier = tbai_inv.tbai_identifier;
                            json.tbai_qr_src = tbai_inv.tbai_qr_src;
                            if (tbai_inv.previous_tbai_invoice !== null) {
                                json.tbai_previous_order_pos_reference =
                                    tbai_inv.previous_tbai_invoice.order.simplified_invoice;
                            }
                        }
                    }
                }
                return json;
            }
            export_for_printing() {
                const receipt = super.export_for_printing(...arguments);
                if (this.pos.company.tbai_enabled) {
                    const tbai_inv = this.tbai_simplified_invoice || null;
                    if (tbai_inv !== null) {
                        receipt.tbai_identifier = tbai_inv.tbai_identifier;
                        receipt.tbai_qr_src = tbai_inv.tbai_qr_src;
                    }
                }
                return receipt;
            }

            async tbai_build_invoice() {
                if (this.tbai_current_invoice.state === "rejected") {
                    this.tbai_current_invoice = Promise.resolve();
                }
                this.tbai_current_invoice = this.tbai_current_invoice.then(async () => {
                    let tbai_inv = null;
                    if (this.check_tbai_conf() && !this.to_invoice) {
                        tbai_inv = new tbai_models.TicketBAISimplifiedInvoice(
                            {},
                            {
                                pos: this.pos,
                                order: this,
                            }
                        );
                        await tbai_inv.build_invoice();
                    }
                    return tbai_inv;
                });
            }
        };
    Registries.Model.extend(Order, L10nEsTicketBAIPosOrder);
});
