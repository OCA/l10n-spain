/** @odoo-module **/

import {Order, PosGlobalState} from "point_of_sale.models";
import {ConnectionLostError} from "@web/core/network/rpc_service";
import Registries from "point_of_sale.Registries";

export const L10nEsPosGlobalState = (OriginalPosGlobalState) =>
    class extends OriginalPosGlobalState {
        async _processData(loadedData) {
            await super._processData(...arguments);
            this.pos_devices = loadedData["pos.device"] || [];
        }

        _set_simplified_invoice_number(config) {
            if (this.config.pos_sequence_by_device) {
                this.get_device().device_simplified_invoice_number =
                    config.device_simplified_invoice_number;
                return;
            }
            super._set_simplified_invoice_number(...arguments);
        }

        get_device() {
            return this.pos_device;
        }

        _get_simplified_invoice_number() {
            if (!this.config.pos_sequence_by_device) {
                return super._get_simplified_invoice_number(...arguments);
            }
            return (
                this.get_device().device_simplified_invoice_prefix +
                this.get_padding_simple_inv(
                    this.get_device().device_simplified_invoice_number,
                    this.get_device().device_simplified_invoice_padding
                )
            );
        }

        get_simple_inv_next_number() {
            if (!this.env.pos.config.pos_sequence_by_device) {
                return super.get_simple_inv_next_number(...arguments);
            }
            // If we had pending orders to sync we want to avoid getting the next number
            // from the DB as we'd be ovelaping the sequence.
            if (this.env.pos.db.get_orders().length) {
                return Promise.reject(new ConnectionLostError());
            }
            return this.env.services.rpc({
                method: "search_read",
                domain: [["id", "=", this.env.pos.get_device().id]],
                fields: ["device_simplified_invoice_number"],
                model: "pos.device",
            });
        }

        _update_sequence_number() {
            if (!this.env.pos.config.pos_sequence_by_device) {
                super._update_sequence_number(...arguments);
            } else if (this.get_device()) {
                // If trying to send lost order when starting POS,
                // device can still not be chosen.
                ++this.get_device().device_simplified_invoice_number;
            }
        }

        async set_device(device) {
            const ret = await this.env.services.rpc({
                method: "lock_device",
                model: "pos.device",
                args: [[device.id]],
            });
            if (ret) {
                device.locked = true;
                this.pos_device = device;
            }
            return ret;
        }

        async unset_device() {
            const device = this.get_device();
            if (device) {
                await this.env.services.rpc({
                    method: "unlock_device",
                    model: "pos.device",
                    args: [[device.id]],
                });
                device.locked = false;
                this.pos_device = false;
            }
        }
    };

Registries.Model.extend(PosGlobalState, L10nEsPosGlobalState);

export const L10nEsPosOrder = (OriginalOrder) =>
    class extends OriginalOrder {
        export_as_JSON() {
            const res = super.export_as_JSON(...arguments);
            res.device = this.pos.get_device();
            return res;
        }
    };

Registries.Model.extend(Order, L10nEsPosOrder);
