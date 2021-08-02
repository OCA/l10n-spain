/* Copyright 2021 Binovo IT Human Project SL
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

odoo.define('l10n_es_ticketbai_pos.tbai_models', function (require) {
    'use strict';

    var core = require('web.core');
    var _t = core._t;

    /* A TicketBAI Simplified Invoice represents a customer's order
    to be exported to the Tax Agency.
    */
    var TicketBAISimplifiedInvoice = Backbone.Model.extend({
        initialize: function (attributes, options) {
            Backbone.Model.prototype.initialize.apply(this, arguments);
            options = options || {};
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
            this.vat_regime_key = '01';
            this.vat_regime_key2 = null;
            this.vat_regime_key3 = null;
            this.unsigned_datas = null;
            this.datas = null;
        },
        build_invoice: function () {
            var self = this;
            var built = new $.Deferred();
            var options = {};
            var deviceId = this.pos.config.tbai_device_serial_number || null;
            // Addon l10n_es_pos -> Order.export_as_JSON()
            var simplified_invoice = null;
            var tbai_json = null;
            // Tested on Epson TM-20II
            // 164 (default pixels with margin '0') * 35 (required QR image width in mm) / 22 (default width in mm) = 260
            // Pixels. 255 is the maximum.
            var qr_options = {
                margin: 0,
                width: 255,
            };

            this.previous_tbai_invoice = this.pos.tbai_last_invoice || null;
            this.expedition_date = new Date();
            simplified_invoice =
                this.order.simplified_invoice || this.pos.get_simple_inv_next_number();
            this.number_prefix = this.pos.config.l10n_es_simplified_invoice_prefix;
            this.number = simplified_invoice.slice(this.number_prefix.length);

            if (this.order.fiscal_position) {
                var tbai_vat_regime_key = this.order.fiscal_position.tbai_vat_regime_key;
                if (tbai_vat_regime_key) {
                    this.vat_regime_key = this.pos.get_tbai_vat_regime_key_code_by_id(
                        tbai_vat_regime_key[0]);
                }
                var tbai_vat_regime_key2 = this.order.fiscal_position.tbai_vat_regime_key2;
                if (tbai_vat_regime_key2) {
                    this.vat_regime_key2 = this.pos.get_tbai_vat_regime_key_code_by_id(
                        tbai_vat_regime_key2[0]);
                }
                var tbai_vat_regime_key3 = this.order.fiscal_position.tbai_vat_regime_key3;
                if (tbai_vat_regime_key3) {
                    this.vat_regime_key3 = this.pos.get_tbai_vat_regime_key_code_by_id(
                        tbai_vat_regime_key3[0]);
                }
            }

            tbai_json = this.export_as_JSON();
            if (!_.isEmpty(tbai_json) && this.pos.tbai_signer !== null) {
                if (typeof deviceId === 'string' || deviceId instanceof String) {
                    options.deviceId = deviceId;
                }
                try {
                    this.unsigned_datas = tbai.toXml(
                        tbai_json.Invoice, tbai_json.PreviousInvoiceId || null,
                        tbai_json.Software, options);
                    this.pos.tbai_signer.sign(this.unsigned_datas).then(function (datas){
                        self.datas = datas;
                        self.signature_value = tbai.getTbaiChainInfo(datas).hash;
                        self.tbai_identifier = tbai.getTbaiId(datas);
                        self.tbai_qr_url = tbai.getTbaiUrlFromBaseURL(
                            datas, self.pos.tbai_qr_base_url);
                        QRCode.toDataURL(self.tbai_qr_url, qr_options).then(function (src) {
                            self.tbai_qr_src = src;
                            built.resolve();
                        }, function (err) {
                            throw new Error(err);
                        });
                    }, function (err) {
                        throw new Error(err);
                    });
                } catch (e) {
                    console.error(e);
                    self.pos.gui.show_popup('error', {
                        title: _t('TicketBAI'),
                        body: e.message,
                    });
                    built.reject();
                }
            } else {
                built.reject();
            }
            return built;
        },
        get_vat_without_country_code: function (vat, country_code) {
            var vat_without_country_code = null;
            vat = vat.toUpperCase();
            country_code = country_code ? country_code.toUpperCase() : null;
            if (country_code && vat.slice(0, country_code.length) === country_code) {
                vat_without_country_code = vat.slice(country_code.length);
            } else {
                vat_without_country_code = vat;
            }
            return vat_without_country_code;
        },
        get_tbai_company_vat: function () {
            var company = this.pos.company;
            return this.get_vat_without_country_code(company.vat, company.country.code);
        },
        get_tbai_partner_vat: function (partner_id) {
            var partner = this.pos.db.get_partner_by_id(partner_id);
            var country_code = this.pos.get_country_code_by_id(partner.country_id[0]);
            if ("ES" === country_code || "02" === partner.tbai_partner_idtype) {
                return this.get_vat_without_country_code(partner.vat, country_code);
            } else {
                return partner.tbai_partner_identification_number;
            }
        },
        export_as_JSON: function () {
            var order_json = this.order !== null && this.order.export_as_JSON() || null;
            var tbai = {};
            var company = this.pos.company;
            var vat_keys = [this.vat_regime_key];

            if (order_json !== null && this.number !== null && this.expedition_date !== null) {
                if (this.vat_regime_key2 !== null) {
                    vat_keys.push(this.vat_regime_key2);
                }
                if (this.vat_regime_key3 !== null) {
                    vat_keys.push(this.vat_regime_key3);
                }
                tbai.Invoice = {
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
                    total: order_json.amount_total,
                    vatKeys: vat_keys,
                };
                if (order_json.partner_id) {
                    var partner = this.pos.db.get_partner_by_id(order_json.partner_id);
                    var country_code = this.pos.get_country_code_by_id(partner.country_id[0]);
                    var zip = partner.zip;
                    var address = (partner.street || '') + ', ' +
                                      (partner.zip || '') + ' ' +
                                      (partner.city || '') + ', ' +
                                      (partner.country_id[1] || '');
                    tbai.Invoice.recipient = {
                        irsId: this.get_tbai_partner_vat(order_json.partner_id),
                        name: partner.name,
                        country: country_code,
                        postal: zip,
                        address: address,
                    };
                }
                if (this.previous_tbai_invoice !== null) {
                    tbai.PreviousInvoiceId = {
                        number: this.previous_tbai_invoice.number,
                        serie: this.previous_tbai_invoice.number_prefix,
                        issuedTime: this.previous_tbai_invoice.expedition_date,
                        hash: this.previous_tbai_invoice.signature_value.substring(0, 100),
                    };
                }
                tbai.Software = {
                    license: company.tbai_license_key,
                    developerIrsId: this.get_tbai_partner_vat(company.tbai_developer_id[0]),
                    name: company.tbai_software_name,
                    version: this.pos.tbai_version,
                };
            }
            return tbai;
        },
        get_tbai_lines_from_json: function (lines_json) {
            var lines = [];
            var line = null;
            lines_json.forEach(function (item) {
                line = item[2];
                lines.push({
                    description: line.tbai_description.substring(0, 250),
                    quantity: line.qty,
                    price: line.tbai_price_unit,
                    discount: line.discount,
                    discount_amount:
                        line.qty * line.tbai_price_unit * line.discount / 100.0,
                    vat: line.tbai_vat_amount,
                    amount: line.tbai_price_without_tax,
                    amountWithVat: line.tbai_price_with_tax,
                });
            });
            return lines;
        },
    });

    return {
        TicketBAISimplifiedInvoice: TicketBAISimplifiedInvoice,
    };
});
