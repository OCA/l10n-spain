/* Copyright 2021 Binovo IT Human Project SL
   License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
*/

odoo.define('l10n_es_ticketbai_pos.models', function (require) {
    'use strict';

    var session = require('web.session');
    var models = require('point_of_sale.models');
    var pos_super = models.PosModel.prototype;
    var order_super = models.Order.prototype;
    var orderLine_super = models.Orderline.prototype;
    var core = require('web.core');
    var _t = core._t;
    var tbai_models = require('l10n_es_ticketbai_pos.tbai_models');
    var rpc = require('web.rpc');

    models.load_fields('res.company', [
        'tbai_enabled', 'tbai_test_enabled', 'tbai_license_key', 'tbai_developer_id',
        'tbai_software_name', 'tbai_tax_agency_id', 'tbai_protected_data', 'tbai_protected_data_txt'
    ]);

    models.load_fields('res.country', ['code']);
    models.load_fields('res.partner', [
        'tbai_partner_idtype', 'tbai_partner_identification_number']);

    models.load_models([
        {
            model:  'res.partner',
            fields: ['vat', 'country_id', 'tbai_partner_idtype', 'tbai_partner_identification_number'],
            condition: function (self, tmp) {
                return self.company.tbai_enabled;
            },
            domain: function (self){ return [['customer','=',false],['id', '=', self.company.tbai_developer_id[0]]]; },
            loaded: function (self, partner){
                if (1 == partner.length && !self.db.get_partner_by_id(partner[0].id)) {
                    self.partners.concat(partner);
                    self.db.add_partners(partner);
                }
            },
        },
        {
            model: 'tbai.invoice',
            fields: ['signature_value', 'number_prefix', 'number', 'expedition_date'],
            condition: function (self, tmp) {
                return self.company.tbai_enabled;
            },
            domain: function (self) {
                return [['id', '=', self.config.tbai_last_invoice_id[0]]];
            },
            loaded: function (self, tbai_invoices) {
                if (Array.isArray(tbai_invoices) && 1 == tbai_invoices.length){
                    var tbai_inv = tbai_invoices[0];
                    var tbai_last_invoice_data = {
                        order: {simplified_invoice: tbai_inv.number_prefix + tbai_inv.number},
                        signature_value: tbai_inv.signature_value,
                        number: tbai_inv.number,
                        number_prefix: tbai_inv.number_prefix,
                        expedition_date: moment(tbai_inv.expedition_date, 'DD-MM-YYYY').toDate()
                    }
                    self.set('tbai_last_invoice_data', tbai_last_invoice_data);
                    }
            }
        },
        {
            model: 'pos.config',
            fields: ['id'],
            condition: function(self, tmp) {
                return self.company.tbai_enabled;
            },
            domain: function (self) { return [['id','=', self.pos_session.config_id[0]]]; },
            loaded: function (self, configs) {
                self.set_tbai_last_invoice_data(self.get_tbai_last_invoice_data());
                return rpc.query({
                    model: 'pos.config',
                    method: 'get_tbai_p12_and_friendlyname',
                    args: [configs[0].id]
                }).then(function (args) {
                    return tbai.TbaiSigner.fromBuffer(
                        atob(args[0]), args[1]
                    ).then(function (signer) {
                        self.tbai_signer = signer;
                    }, function (err) {
                        console.error(err);
                    });
                });
            }
        },
        {
            model: 'tbai.tax.agency',
            fields: ['version', 'qr_base_url', 'test_qr_base_url'],
            condition: function (self, tmp) {
                return self.company.tbai_enabled;
            },
            domain: function (self) {
                return [['id', '=', self.company.tbai_tax_agency_id[0]]];
            },
            loaded: function (self, tax_agencies) {
                self.tbai_version = tax_agencies[0].version;
                if (self.company.tbai_test_enabled) {
                    self.tbai_qr_base_url = tax_agencies[0].test_qr_base_url;
                } else {
                    self.tbai_qr_base_url = tax_agencies[0].qr_base_url;
                }
            }
        },
        {
            model: 'tbai.vat.regime.key',
            fields: ['code'],
            condition: function (self, tmp) {
                return self.company.tbai_enabled;
            },
            domain: function (self) {
                return [];
            },
            loaded: function (self, vat_regime_keys) {
                self.tbai_vat_regime_keys = vat_regime_keys;
            }
        },
    ]);

    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            this.tbai_version = null;
            this.tbai_signer = null;
            this.tbai_qr_base_url = null;
            this.tbai_vat_regime_keys = null;
            this.set({'tbai_last_invoice_data': null});
            pos_super.initialize.apply(this, arguments);
        },
        get_country_by_id: function (id) {
            var countries = this.countries;
            var country = null;
            var i = 0;
            while (country === null && i < countries.length) {
                if (id === countries[i].id) {
                    country = countries[i];
                }
                i++;
            }
            return country;
        },
        get_country_code_by_id: function (id) {
            var country = this.get_country_by_id(id);
            return country && country.code.toUpperCase() || null;
        },
        get_tbai_vat_regime_key_by_id: function (id) {
            var vat_regime_keys = this.tbai_vat_regime_keys;
            var vat_regime_key = null;
            var i = 0;
            while (vat_regime_key === null && i < vat_regime_keys.length) {
                if (id === vat_regime_keys[i].id) {
                    vat_regime_key = vat_regime_keys[i];
                }
                i++;
            }
            return vat_regime_key;
        },
        get_tbai_vat_regime_key_code_by_id: function (id) {
            var tbai_vat_regime_key = this.get_tbai_vat_regime_key_by_id(id);
            return tbai_vat_regime_key && tbai_vat_regime_key.code || null;
        },
        push_order: function (order, opts) {
            var self = this;
            if (this.company.tbai_enabled && order) {
                return order.tbai_current_invoice.then(function (tbai_inv) {
                    var tbai_last_invoice_data = {
                        order: {simplified_invoice: tbai_inv.number_prefix + tbai_inv.number},
                        signature_value: tbai_inv.signature_value,
                        number: tbai_inv.number,
                        number_prefix: tbai_inv.number_prefix,
                        expedition_date: tbai_inv.expedition_date
                    };
                    self.set_tbai_last_invoice_data(tbai_last_invoice_data);
                    return pos_super.push_order.call(self, order, opts);
                });
            } else {
                return pos_super.push_order.call(self, order, opts);
            }
        },
        get_tbai_last_invoice_data: function() {
            var db_json_last_invoice_data = this.db.get_tbai_json_last_invoice_data();
            if (!(Object.keys(db_json_last_invoice_data).length === 0)) {
                return db_json_last_invoice_data;
            }
            else {
                return this.get('tbai_last_invoice_data') || null;
            }
        },
        set_tbai_last_invoice_data: function(data) {
            this.set('tbai_last_invoice_data', data);
            this.db.set_tbai_json_last_invoice_data(data);
        },
        scan_product: function (parsed_code) {
            var res = true;
            var ok = true;
            if (this.company.tbai_enabled) {
                var product = this.db.get_product_by_barcode(parsed_code.base_code);
                if (!product) {
                    res = false;
                } else if (1 !== product.taxes_id.length) {
                    ok = false;
                    this.gui.show_popup('error', {
                        title: _t('TicketBAI'),
                        body: _.str.sprintf(_t('Please set a tax for product %s.'), product.display_name)
                    });
                }
            }
            if (ok) {
                res = pos_super.scan_product.call(this, parsed_code);
            } else {
                res = true;
            }
            return res;
        },
    });

    models.Orderline = models.Orderline.extend({
        export_as_JSON: function () {
            var json = orderLine_super.export_as_JSON.apply(this, arguments);
            if (this.pos.company.tbai_enabled) {
                var mapped_included_taxes = [];
                var product = this.get_product();
                var price_unit = null;
                var tax = this.get_taxes()[0];
                json.tbai_description = product.display_name || "";
                if (tax) {
                    json.tbai_vat_amount = tax.amount;
                    json.tbai_price_without_tax = this.get_price_without_tax();
                    json.tbai_price_with_tax = this.get_price_with_tax();
                    var fp_taxes = this._map_tax_fiscal_position(tax);
                    if (tax.price_include && _.contains(fp_taxes, tax)) {
                        mapped_included_taxes.push(tax);
                    }
                }
                if (mapped_included_taxes.length > 0) {
                    price_unit = this.compute_all(
                        mapped_included_taxes, json.price_unit, 1,
                        this.pos.currency.rounding, true).total_excluded;
                } else {
                    price_unit = json.price_unit;
                }
                json.tbai_price_unit = price_unit;
            }
            return json;
        },
    });

    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            var self = this;
            this.tbai_simplified_invoice = null;
            this.tbai_current_invoice = $.when();
            order_super.initialize.apply(this, arguments);
            return this;
        },
        check_products_have_taxes: function () {
            var orderLines = this.get_orderlines();
            var product = null;
            var line = null;
            var taxes = null;
            var all_products_have_one_tax = true;
            var i = 0;
            while (all_products_have_one_tax && i < orderLines.length) {
                line = orderLines[i];
                taxes = line.get_taxes();
                product = line.get_product();
                if (1 != taxes.length) {
                    all_products_have_one_tax = false;
                }
                i++;
            }
            return all_products_have_one_tax;
        },
        check_company_vat: function () {
            return this.pos.company.vat ? true : false;
        },
        check_customer_country_code: function (customer=null) {
            var customer = customer || this.get_client();
            return !customer || (customer && !customer.country_id) ? false : true;
        },
        check_simplified_invoice_spanish_customer: function (customer=null) {
            var country_code;
            var customer = customer || this.get_client();
            var ok = true;
            if (customer != null) {
                ok = this.check_customer_country_code(customer);
                if (ok) {
                    country_code = this.pos.get_country_code_by_id(customer.country_id[0]);
                    if ("ES" !== country_code && !this.to_invoice) {
                        ok = false;
                    }
                }
            }
            return ok;
        },
        check_customer_vat: function (customer=null) {
            var country_code;
            var customer = customer || this.get_client();
            var ok = true;
            if (customer != null) {
                ok = this.check_customer_country_code(customer);
                if (ok) {
                    country_code = this.pos.get_country_code_by_id(customer.country_id[0]);
                    if ("ES" === country_code) {
                        if (!customer.vat) {
                            ok = false;
                        }
                    } else {
                        if ("02" === customer.tbai_partner_idtype && !customer.vat) {
                            ok = false;
                        } else if ("02" !== customer.tbai_partner_idtype && !customer.tbai_partner_identification_number) {
                            ok = false;
                        }
                    }
                }
            }
            return ok;
        },
        check_fiscal_position_vat_regime_key: function () {
            var ok = true;
            if (this.fiscal_position && !this.fiscal_position.tbai_vat_regime_key) {
                ok = false;
            }
            return ok;
        },
        check_tbai_conf: function () {
            return this.check_company_vat() &&
                this.check_simplified_invoice_spanish_customer() &&
                this.check_customer_vat() &&
                this.check_fiscal_position_vat_regime_key() &&
                this.check_products_have_taxes();
        },
        export_as_JSON: function () {
            var datas;
            var signature_value;
            var previous_order;
            var tbai_inv;
            var json = order_super.export_as_JSON.apply(this, arguments);
            if (this.pos.company.tbai_enabled) {
                var taxLines = [];
                var order = this;
                this.get_tax_details().forEach(function (taxDetail) {
                    var taxLineDict = taxDetail;
                    taxLineDict.baseAmount = order.get_base_by_tax()[taxDetail.tax.id];
                    taxLines.push([0, 0, taxLineDict]);});
                json.taxLines = taxLines;
                tbai_inv = this.tbai_simplified_invoice || null;
                if (tbai_inv !== null) {
                    datas = tbai_inv.datas;
                    signature_value = tbai_inv.signature_value;
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
        },
        export_for_printing: function () {
            var receipt = order_super.export_for_printing.apply(this, arguments);
            if (this.pos.company.tbai_enabled) {
                var tbai_inv = this.tbai_simplified_invoice || null;
                if (tbai_inv !== null) {
                    receipt.tbai_identifier = tbai_inv.tbai_identifier;
                    receipt.tbai_qr_src = tbai_inv.tbai_qr_src;
                }
            }
            return receipt;
        },
        tbai_build_invoice: function () {
            var self = this;
            if (self.tbai_current_invoice.state() == 'rejected') {
                self.tbai_current_invoice = new $.when();
            }
            self.tbai_current_invoice = self.tbai_current_invoice.then(function () {
                var tbai_current_invoice = $.when();
                var tbai_inv = null;
                var ok = self.check_tbai_conf();
                if (ok && !self.to_invoice) {
                    tbai_inv = new tbai_models.TicketBAISimplifiedInvoice({}, {
                        pos: self.pos, order: self
                    });
                    tbai_current_invoice = tbai_inv.build_invoice().then(function () {
                        return tbai_inv;
                    });
                }
                return tbai_current_invoice;
            });
        },
    });
});
