import {ConnectionLostError} from "@web/core/network/rpc";
import {PosStore} from "@point_of_sale/app/store/pos_store";
import {patch} from "@web/core/utils/patch";

patch(PosStore.prototype, {
    /**
     * Returns the currently selected physical device.
     */
    getDevice() {
        return this._pos_device;
    },

    /**
     * Locks the device on the server and stores it locally.
     */
    async setDevice(device) {
        const ret = await this.data.call("pos.device", "lock_device", [[device.id]]);
        if (ret) {
            device.locked = true;
            this._pos_device = device;
        }
        return ret;
    },

    /**
     * Unlocks the current device on the server and clears the local reference.
     */
    async unsetDevice() {
        const device = this.getDevice();
        if (device) {
            await this.data.call("pos.device", "unlock_device", [[device.id]]);
            device.locked = false;
            this._pos_device = undefined;
        }
    },

    /**
     * When device-based sequencing is enabled, store the number on the device
     * instead of the config.
     */
    setSimplifiedInvoiceNumber(number) {
        if (!this.config.pos_sequence_by_device) {
            return super.setSimplifiedInvoiceNumber(...arguments);
        }
        const device = this.getDevice();
        if (device) {
            device.device_simplified_invoice_number = number;
        }
    },

    /**
     * When device-based sequencing is enabled, return the device counter.
     */
    getCurrentSimplifiedInvoiceNumber() {
        if (!this.config.pos_sequence_by_device) {
            return super.getCurrentSimplifiedInvoiceNumber(...arguments);
        }
        const device = this.getDevice();
        return device ? device.device_simplified_invoice_number : 1;
    },

    /**
     * When device-based sequencing is enabled, generate the unique ID from
     * the device sequence instead of the config sequence.
     */
    getSimplifiedUniqueId() {
        if (!this.config.pos_sequence_by_device) {
            return super.getSimplifiedUniqueId(...arguments);
        }
        const device = this.getDevice();
        return (
            device.device_simplified_invoice_prefix +
            this._getPaddingSimpleInv(
                device.device_simplified_invoice_number,
                device.device_simplified_invoice_padding
            )
        );
    },

    /**
     * When device-based sequencing is enabled, increment the device counter
     * instead of the config counter.
     */
    incrementSimplifiedInvoiceNumber() {
        if (!this.config.pos_sequence_by_device) {
            return super.incrementSimplifiedInvoiceNumber(...arguments);
        }
        const device = this.getDevice();
        if (device) {
            device.device_simplified_invoice_number += 1;
        }
    },

    /**
     * When device-based sequencing is enabled, fetch the next number from the
     * device sequence instead of the config sequence.
     */
    async getSimpleInvNextNumber() {
        if (!this.config.pos_sequence_by_device) {
            return super.getSimpleInvNextNumber(...arguments);
        }
        // Protect against sequence overlap when there are unsynced orders.
        if (this.hasPendingOrders()) {
            return Promise.reject(new ConnectionLostError());
        }
        const device = this.getDevice();
        try {
            const result = await this.data.searchRead(
                "pos.device",
                [["id", "=", device.id]],
                ["device_simplified_invoice_number"]
            );
            device.device_simplified_invoice_number =
                result[0]?.device_simplified_invoice_number || 1;
        } catch (error) {
            if (!this.hasPendingOrders()) {
                device.device_simplified_invoice_number += 1;
            }
            console.error(error);
        }
        return device.device_simplified_invoice_number;
    },

    /**
     * @override
     * Unlock the device before opening the closing popup.
     */
    async closeSession() {
        if (this.config.pos_sequence_by_device) {
            await this.unsetDevice();
        }
        return super.closeSession(...arguments);
    },
});
