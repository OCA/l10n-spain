/* Copyright 2021 Binovo IT Human Project SL
   Copyright 2022 Landoo Sistemas de Informacion SL
   Copyright 2022 Advanced Programming Solu SL
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

odoo.define("l10n_es_ticketbai_pos.tbai_models", function (require) {
    "use strict";

    const {Gui} = require("point_of_sale.Gui");
    const field_utils = require("web.field_utils");

    const QRCode = window.QRCode;
    const core = require("web.core");
    const _t = core._t;
    const tbai = window.tbai;

    /* A TicketBAI Simplified Invoice represents a customer's order
    to be exported to the Tax Agency.
    */
    class TicketBAISimplifiedInvoice {
        constructor(attributes, options = {}) {
            this.pos = options.pos;
            this.previous_tbai_invoice = null;
            this.order = options.order || null;
            this.number = options.number || null;
            this.number_prefix = options.number_prefix || null;
            this.expedition_date = options.expedition_date || null;
            this.signature_value = options.signature_value || null;
            this.tbai_identifier = options.tbai_identifier || null;
            this.tbai_qr_src = options.tbai_qr_src || null;
            this.tbai_qr_url = null;
            this.vat_regime_key = "01";
            this.vat_regime_key2 = null;
            this.vat_regime_key3 = null;
            this.unsigned_datas = null;
            this.datas = null;
            // Tested on Epson TM-20II
            // 164 (default pixels with margin '0') * 35 (required QR image width in mm) / 22 (default width in mm) = 260
            // Pixels. 255 is the maximum.
            this.qr_options = {
                margin: 0,
                width: 255,
            };
        }

        async build_invoice() {
            if (this._building) {
                return Promise.reject(
                    new Error("Invoice already being built. Please wait.")
                );
            }

            this._building = true;
            try {
                const deviceId = this.pos.config.tbai_device_serial_number || null;

                const transaction = {
                    previous_tbai_invoice: null,
                    expedition_date: null,
                    number: null,
                    number_prefix: null,
                    vat_regime_key: "01",
                    vat_regime_key2: null,
                    vat_regime_key3: null,
                    unsigned_datas: null,
                    datas: null,
                    signature_value: null,
                    tbai_identifier: null,
                    tbai_qr_url: null,
                    tbai_qr_src: null,
                };

                try {
                    // Step 1-3: Build transaction (no mutations to `this` yet)
                    transaction.previous_tbai_invoice =
                        this.pos.get_tbai_last_invoice_data();
                    transaction.expedition_date = new Date();
                    console.log(
                        "[TicketBAI] Step 1: Set expedition_date:",
                        transaction.expedition_date
                    );

                    if (this.pos.config.pos_sequence_by_device) {
                        transaction.number_prefix =
                            this.pos.get_device().device_simplified_invoice_prefix;
                        transaction.number =
                            transaction.number_prefix +
                            this.pos.get_padding_simple_inv(
                                this.pos.get_device().device_simplified_invoice_number,
                                this.pos.get_device().device_simplified_invoice_padding
                            );
                    } else {
                        transaction.number_prefix =
                            this.pos.config.l10n_es_simplified_invoice_prefix;
                        transaction.number =
                            this.order.simplified_invoice ||
                            transaction.number_prefix +
                                this.pos.get_padding_simple_inv(
                                    this.pos.config.l10n_es_simplified_invoice_number,
                                    this.pos.config.l10n_es_simplified_invoice_padding
                                );
                    }

                    // Extract numeric part from full number
                    const numericPart = transaction.number.slice(
                        transaction.number_prefix.length
                    );
                    console.log("[TicketBAI] Step 2: Set number and number_prefix:", {
                        number_prefix: transaction.number_prefix,
                        number: numericPart,
                    });

                    if (this.order.fiscal_position) {
                        const tbai_vat_regime_key =
                            this.order.fiscal_position.tbai_vat_regime_key;
                        if (tbai_vat_regime_key) {
                            const id_vat_regime_key =
                                this.order.fiscal_position.tbai_vat_regime_key[0];
                            const object_vat_regime_key =
                                this.pos.tbai_vat_regime_keys.find(
                                    (x) => x.id === id_vat_regime_key
                                );
                            transaction.vat_regime_key = object_vat_regime_key.code;
                        }
                        const tbai_vat_regime_key2 =
                            this.order.fiscal_position.tbai_vat_regime_key2;
                        if (tbai_vat_regime_key2) {
                            const id_vat_regime_key =
                                this.order.fiscal_position.tbai_vat_regime_key2[0];
                            const object_vat_regime_key =
                                this.pos.tbai_vat_regime_keys.find(
                                    (x) => x.id === id_vat_regime_key
                                );
                            transaction.vat_regime_key2 = object_vat_regime_key.code;
                        }
                        const tbai_vat_regime_key3 =
                            this.order.fiscal_position.tbai_vat_regime_key3;
                        if (tbai_vat_regime_key3) {
                            const id_vat_regime_key =
                                this.order.fiscal_position.tbai_vat_regime_key3[0];
                            const object_vat_regime_key =
                                this.pos.tbai_vat_regime_keys.find(
                                    (x) => x.id === id_vat_regime_key
                                );
                            transaction.vat_regime_key3 = object_vat_regime_key.code;
                        }
                    }
                    console.log("[TicketBAI] Step 3: Set VAT regime keys:", {
                        vat_regime_key: transaction.vat_regime_key,
                        vat_regime_key2: transaction.vat_regime_key2,
                        vat_regime_key3: transaction.vat_regime_key3,
                    });

                    // Step 4-11: Critical operations
                    // ATOMIC COMMIT BEFORE export_as_JSON: Sync transaction to instance
                    Object.assign(this, transaction);

                    const tbai_json = this.export_as_JSON();
                    if (_.isEmpty(tbai_json) || !this.pos.tbai_signer) {
                        throw new Error("TBAI JSON is empty or TBAI signer is null");
                    }

                    // Generate all critical data before any mutations
                    const criticalData = await this._generateCriticalData(
                        tbai_json,
                        deviceId
                    );

                    // FINAL ATOMIC COMMIT: Update instance with critical data
                    Object.assign(transaction, criticalData);
                    Object.assign(this, transaction);

                    // Validate state after atomic commit
                    this._validateState();

                    return Promise.resolve();
                } catch (error) {
                    console.error("[TicketBAI] Error in build_invoice():", error);
                    Gui.showPopup("ErrorPopup", {
                        title: _t("TicketBAI"),
                        body: error.message,
                    });
                    return Promise.reject(error);
                }
            } finally {
                this._building = false;
            }
        }

        async _generateCriticalData(tbai_json, deviceId) {
            const options = {};
            if (typeof deviceId === "string" || deviceId instanceof String) {
                options.deviceId = deviceId;
            }

            // Generate all data in isolated scope
            const unsigned_datas = tbai.toXml(
                tbai_json.Invoice,
                tbai_json.PreviousInvoiceId || null,
                tbai_json.Software,
                options
            );

            const datas = await this.pos.tbai_signer.sign(unsigned_datas);
            const signature_value = tbai.getTbaiChainInfo(datas).hash;
            const tbai_identifier = tbai.getTbaiId(datas);
            const tbai_qr_url = tbai.getTbaiUrlFromBaseURL(
                datas,
                this.pos.tbai_qr_base_url
            );
            const tbai_qr_src = await QRCode.toDataURL(tbai_qr_url, this.qr_options);

            return {
                unsigned_datas,
                datas,
                signature_value,
                tbai_identifier,
                tbai_qr_url,
                tbai_qr_src,
            };
        }

        _validateState() {
            const requiredFields = [
                "datas",
                "signature_value",
                "tbai_identifier",
                "tbai_qr_src",
            ];

            const missing = requiredFields.filter((field) => !this[field]);
            if (missing.length > 0) {
                throw new Error(`Missing critical fields: ${missing.join(", ")}`);
            }
        }

        get_vat_without_country_code(vat, country_code) {
            const vat_upper = vat.toUpperCase();
            const country_code_upper = country_code ? country_code.toUpperCase() : "";
            return vat_upper.startsWith(country_code_upper)
                ? vat_upper.slice(country_code_upper.length)
                : vat_upper;
        }

        get_tbai_company_vat() {
            const {vat, country} = this.pos.company;
            return this.get_vat_without_country_code(vat, country.code);
        }

        get_tbai_partner_vat(partner_id) {
            const partner = this.pos.db.get_partner_by_id(partner_id);
            const country_code = this.pos.get_country_code_by_id(partner.country_id[0]);
            if (country_code === "ES" || partner.tbai_partner_idtype === "02") {
                return this.get_vat_without_country_code(partner.vat, country_code);
            }
            return partner.tbai_partner_identification_number;
        }

        get_tbai_lines_from_json(lines_json) {
            const lines = [];
            const company = this.pos.company;
            lines_json.forEach((item) => {
                const line = item[2];
                let description_line = line.tbai_description.substring(0, 250);
                if (company.tbai_protected_data && company.tbai_protected_data_txt) {
                    description_line = company.tbai_protected_data_txt.substring(
                        0,
                        250
                    );
                }
                lines.push({
                    description: description_line,
                    quantity: line.qty,
                    price: field_utils.parse.float(
                        this.pos.format_currency_no_symbol(line.tbai_price_unit)
                    ),
                    discount: field_utils.parse.float(
                        this.pos.format_currency_no_symbol(line.discount)
                    ),
                    discountAmount: field_utils.parse.float(
                        this.pos.format_currency_no_symbol(
                            (line.qty * line.tbai_price_unit * line.discount) / 100.0
                        )
                    ),
                    vat: line.tbai_vat_amount,
                    amount: field_utils.parse.float(
                        this.pos.format_currency_no_symbol(line.tbai_price_without_tax)
                    ),
                    amountWithVat: field_utils.parse.float(
                        this.pos.format_currency_no_symbol(line.tbai_price_with_tax)
                    ),
                });
            });
            return lines;
        }

        get_tbai_vat_lines_from_json(order_json) {
            const vatLines = [];
            const vatLinesJson = order_json.taxLines;
            if (vatLinesJson && vatLinesJson.length > 0) {
                vatLinesJson.forEach((vatLineJson) => {
                    const vatLine = vatLineJson[2];
                    vatLines.push({
                        base: field_utils.parse.float(
                            this.pos.format_currency_no_symbol(vatLine.baseAmount)
                        ),
                        rate: vatLine.tax.amount,
                        amount: field_utils.parse.float(
                            this.pos.format_currency_no_symbol(vatLine.amount)
                        ),
                    });
                });
            } else {
                const fline = order_json.lines[0][2];
                vatLines.push({
                    base: field_utils.parse.float(
                        this.pos.format_currency_no_symbol(order_json.amount_total)
                    ),
                    rate: fline.tbai_vat_amount,
                    amount: 0,
                });
            }
            return vatLines;
        }

        export_as_JSON() {
            const order_json =
                (this.order !== null && this.order.export_as_JSON()) || null;
            const tbai_json = {};
            const company = this.pos.company;
            const vat_keys = [this.vat_regime_key];
            const simplified = company.tbai_vat_regime_simplified ? "S" : "N";

            if (
                order_json !== null &&
                this.number !== null &&
                this.expedition_date !== null
            ) {
                if (this.vat_regime_key2 !== null) {
                    vat_keys.push(this.vat_regime_key2);
                }
                if (this.vat_regime_key3 !== null) {
                    vat_keys.push(this.vat_regime_key3);
                }
                tbai_json.Invoice = {
                    simple: true,
                    issuer: {
                        irsId: this.get_tbai_company_vat(),
                        name: company.name,
                    },
                    id: {
                        number: this.number,
                        serie: this.number_prefix,
                        issuedTime: this.expedition_date,
                    },
                    description: {
                        text: order_json.name,
                        operationDate: this.expedition_date,
                    },
                    lines: this.get_tbai_lines_from_json(order_json.lines),
                    total: field_utils.parse.float(
                        this.pos.format_currency_no_symbol(order_json.amount_total)
                    ),
                    vatKeys: vat_keys,
                    simplified: simplified,
                };
                tbai_json.Invoice.vatLines =
                    this.get_tbai_vat_lines_from_json(order_json);
                if (order_json.partner_id) {
                    const partner = this.pos.db.get_partner_by_id(
                        order_json.partner_id
                    );
                    const zip = partner.zip;
                    const address = `${partner.street || ""}, ${partner.zip || ""} ${
                        partner.city || ""
                    }, ${partner.country_id[1] || ""}`;
                    tbai_json.Invoice.recipient = {
                        irsId: this.get_tbai_partner_vat(order_json.partner_id),
                        name: partner.name,
                        postal: zip,
                        address: address,
                    };
                }
                if (this.previous_tbai_invoice !== null) {
                    tbai_json.PreviousInvoiceId = {
                        number: this.previous_tbai_invoice.number,
                        serie: this.previous_tbai_invoice.number_prefix,
                        issuedTime: new Date(
                            JSON.parse(
                                JSON.stringify(
                                    this.previous_tbai_invoice.expedition_date
                                )
                            )
                        ),
                        hash: this.previous_tbai_invoice.signature_value.substring(
                            0,
                            100
                        ),
                    };
                }
                tbai_json.Software = {
                    license: company.tbai_license_key,
                    developerIrsId: this.get_tbai_partner_vat(
                        company.tbai_developer_id[0]
                    ),
                    name: company.tbai_software_name,
                    version: company.tbai_software_version,
                };
            }
            return tbai_json;
        }
    }

    return {
        TicketBAISimplifiedInvoice,
    };
});
