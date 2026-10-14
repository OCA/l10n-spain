import logging
from collections import OrderedDict

import psycopg2
import pytz

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.service.model import PG_CONCURRENCY_ERRORS_TO_RETRY

from odoo.addons.l10n_es_verifactu_oca.models.verifactu_mixin import (
    VerifactuChainingLocked,
)

_logger = logging.getLogger(__name__)

VERIFACTU_VALID_POS_STATES = ["paid", "done"]


class PosOrder(models.Model):
    _name = "pos.order"
    _inherit = ["pos.order", "verifactu.mixin"]

    verifactu_chaining_attempts = fields.Integer(
        string="VERI*FACTU chaining attempts",
        copy=False,
        readonly=True,
        # Needed: without it the column is NULL, and `<` does not match NULL,
        # so the sweep would not see the orders it exists to recover.
        default=0,
        help="Number of times the chaining of this order has been attempted "
        "and failed. Used by the recovery cron to stop retrying an order that "
        "cannot be chained.",
    )

    @api.depends(
        "company_id",
        "company_id.verifactu_enabled",
        "company_id.verifactu_start_date",
        "date_order",
        "fiscal_position_id",
        "fiscal_position_id.aeat_active",
        "session_id",
        "session_id.config_id",
        "session_id.config_id.journal_id",
        "session_id.config_id.journal_id.verifactu_enabled",
    )
    def _compute_verifactu_enabled(self):
        """Compute if the POS order is enabled for the veri*FACTU"""
        for order in self:
            # Check if journal is verifactu enabled
            journal_enabled = (
                order.session_id
                and order.session_id.config_id
                and order.session_id.config_id.journal_id
                and order.session_id.config_id.journal_id.verifactu_enabled
            )

            if (
                order.company_id.verifactu_enabled
                and journal_enabled
                and (
                    not order.company_id.verifactu_start_date
                    or order.date_order
                    and order.date_order.date() >= order.company_id.verifactu_start_date
                )
            ):
                order.verifactu_enabled = (
                    order.fiscal_position_id and order.fiscal_position_id.aeat_active
                ) or not order.fiscal_position_id
            else:
                order.verifactu_enabled = False

    @api.depends("fiscal_position_id")
    def _compute_verifactu_tax_key(self):
        for order in self:
            order.verifactu_tax_key = order.fiscal_position_id.verifactu_tax_key or "01"

    @api.depends("fiscal_position_id")
    def _compute_verifactu_registration_key(self):
        for order in self:
            if order.fiscal_position_id:
                key = order.fiscal_position_id.verifactu_registration_key
                if key:
                    order.verifactu_registration_key = key
            else:
                domain = [
                    ("code", "=", "01"),
                    (
                        "verifactu_tax_key",
                        "=",
                        "01",
                    ),
                ]
                verifactu_key_obj = self.env["verifactu.registration.key"]
                order.verifactu_registration_key = verifactu_key_obj.search(
                    domain, limit=1
                )

    @api.model
    def _process_order(self, order, draft, existing_order):
        pos_order_id = super()._process_order(order, draft, existing_order)
        pos_order = self.env["pos.order"].browse(pos_order_id)

        if not pos_order._is_verifactu_order():
            return pos_order_id

        pos_order.verifactu_registration_date = fields.Datetime.now()

        try:
            pos_order._generate_verifactu_chaining()
        except Exception as e:  # noqa: BLE001 -- see below
            if (
                isinstance(e, psycopg2.OperationalError)
                and e.pgcode in PG_CONCURRENCY_ERRORS_TO_RETRY
            ):
                # Odoo retries the whole request on these, which is a better
                # answer than marking the order: the sync has written nothing
                # yet that the retry would duplicate. A lock collision on the
                # chaining row does not reach here -- verifactu_mixin turns it
                # into VerifactuChainingLocked.
                raise
            # Not re-raised: the sale is already paid and the cashier cannot
            # fix a chaining problem. Marked instead, so it is not lost.
            # Every exception counts, not only UserError: a database error
            # escaping here aborts the whole sync, so the sale never reaches
            # the backend and its simplified invoice number is burnt anyway.
            # Writing the mark is safe because the chaining SQL runs inside a
            # savepoint, so the cursor is usable again once it fails.
            _logger.exception(
                "[ID: %d, REF: %s, INV: %s] Failed to create verifactu chaining: %s",
                pos_order.id,
                pos_order.pos_reference,
                pos_order.l10n_es_unique_id,
                str(e),
            )
            pos_order._mark_verifactu_chaining_failure(
                e, spend_attempt=not isinstance(e, VerifactuChainingLocked)
            )

        return pos_order_id

    def _mark_verifactu_chaining_failure(self, error, spend_attempt=True):
        """Leave a visible trace of a chaining failure on the order.

        Reuses the aeat.mixin error fields, which the form view and the
        "VERI*FACTU failed" search filter already show.
        """
        self.ensure_one()
        vals = {"aeat_send_failed": True, "aeat_send_error": str(error)}
        if spend_attempt:
            # Only a failure that will not fix itself spends budget: counting
            # the transient ones abandons chainable sales after a busy spell.
            vals["verifactu_chaining_attempts"] = self.verifactu_chaining_attempts + 1
        self.write(vals)

    def _generate_pos_order_invoice(self):
        res = super()._generate_pos_order_invoice()
        # Once invoiced the sale is registered through the invoice, so the
        # pending failure is moot and nothing else would ever clear it. The
        # invoice must be registered for real, though: it goes through another
        # journal, which may well have VERI*FACTU disabled.
        stale = self.filtered(
            lambda order: order.aeat_send_failed
            and not order.last_verifactu_invoice_entry_id
            and order.account_move.last_verifactu_invoice_entry_id
        )
        if stale:
            stale.write({"aeat_send_failed": False, "aeat_send_error": False})
        return res

    def _is_verifactu_order(self):
        """Whether this order must be registered in VERI*FACTU.

        The state check is part of the guard, not an afterthought: the chain is
        append-only, so an order that is not a closed sale yet must never take
        a link in it. Its hash string would be empty
        (see _get_verifactu_hash_string) and the chain would carry the SHA-256
        of an empty string for a sale that may never happen.
        """
        self.ensure_one()
        return (
            self.exists()
            and not self.to_invoice
            and self.verifactu_enabled
            and self.state in VERIFACTU_VALID_POS_STATES
        )

    def _is_refund_order(self):
        """Check if this POS order is a refund"""
        self.ensure_one()
        return self.amount_total < 0

    def _get_verifactu_document_type(self):
        if self._is_refund_order():
            return "R5"  # Refund for simplified invoices
        return "F2"  # Regular simplified invoice for POS orders

    def _get_verifactu_description(self):
        return self.verifactu_description or self.company_id.verifactu_description

    def _get_verifactu_chaining(self):
        """Return the verifactu chaining for this POS order.

        For POS orders, we use the company-wide chaining like invoices.
        TODO: Allow the user to setup a new chaining for each PoS Config.
        """
        return self.company_id.verifactu_chaining_id

    def _get_verifactu_previous_hash(self):
        """Get the previous hash from the verifactu invoice entry chain."""
        if self.last_verifactu_invoice_entry_id:
            return self.last_verifactu_invoice_entry_id.previous_hash or ""
        return ""

    def _get_verifactu_registration_date(self):
        """Get the registration date in ISO 8601 format."""
        if not self.verifactu_registration_date:
            return ""
        # Date format must be ISO 8601
        return (
            pytz.utc.localize(self.verifactu_registration_date)
            .astimezone()
            .isoformat(timespec="seconds")
        )

    def _get_document_date(self):
        return self.date_order

    def _get_document_fiscal_date(self):
        return self.date_order

    def _get_valid_document_states(self):
        return VERIFACTU_VALID_POS_STATES

    def _get_document_serial_number(self):
        return (self.l10n_es_unique_id or self.pos_reference)[0:60]

    def _get_mapping_key(self):
        return "out_invoice"

    def _get_verifactu_issuer(self):
        return self.company_id.partner_id._parse_aeat_vat_info()[2]

    def _verifactu_get_partner(self):
        """Get the partner for AEAT purposes"""
        return (
            self.partner_id.commercial_partner_id
            if self.partner_id
            else self.env["res.partner"]
        )

    @api.depends("amount_total")
    def _compute_verifactu_refund_type(self):
        """Compute refund type for POS orders"""
        for order in self:
            if order._is_refund_order():
                order.verifactu_refund_type = "I"  # By differences
            else:
                order.verifactu_refund_type = False

    def _get_verifactu_qr_values(self):
        """Get the QR values for the verifactu"""
        self.ensure_one()
        _taxes_dict, _amount_tax, amount_total = self._get_verifactu_taxes_and_total()
        return OrderedDict(
            [
                ("nif", self._get_verifactu_issuer()),
                ("numserie", self._get_document_serial_number()),
                (
                    "fecha",
                    self._change_date_format(self._get_document_fiscal_date()),
                ),
                ("importe", f"{amount_total:.2f}"),
            ]
        )

    def _get_verifactu_hash_string(self, cancel=False):
        """Gets the verifactu hash string"""
        if (
            not self.verifactu_enabled
            or self.state not in VERIFACTU_VALID_POS_STATES
            or self.is_invoiced
        ):
            return ""
        issuer = self._get_verifactu_issuer()
        serial_number = self._get_document_serial_number()
        expedition_date = self._change_date_format(self._get_document_date())
        document_type = self._get_verifactu_document_type()
        _taxes_dict, amount_tax, amount_total = self._get_verifactu_taxes_and_total()
        amount_tax = round(amount_tax, 2)
        amount_total = round(amount_total, 2)
        previous_hash = self._get_verifactu_previous_hash()
        registration_date = self._get_verifactu_registration_date()
        verifactu_hash_string = (
            f"IDEmisorFactura={issuer}&"
            f"NumSerieFactura={serial_number}&"
            f"FechaExpedicionFactura={expedition_date}&"
            f"TipoFactura={document_type}&"
            f"CuotaTotal={amount_tax}&"
            f"ImporteTotal={amount_total}&"
            f"Huella={previous_hash}&"
            f"FechaHoraHusoGenRegistro={registration_date}"
        )
        return verifactu_hash_string

    def _get_verifactu_invoice_dict_out(self, cancel=False):
        """Build dict with data to send to AEAT WS for POS orders."""
        self.ensure_one()
        document_date = self._change_date_format(self._get_document_date())
        company = self.company_id
        serial_number = self._get_document_serial_number()
        taxes_dict, amount_tax, amount_total = self._get_verifactu_taxes_and_total()
        company_vat = company.partner_id._parse_aeat_vat_info()[2]
        verifactu_doc_type = self._get_verifactu_document_type()
        inv_dict = {
            "IDVersion": self._get_verifactu_version(),
            "IDFactura": {
                "IDEmisorFactura": company_vat,
                "NumSerieFactura": serial_number,
                "FechaExpedicionFactura": document_date,
            },
            "NombreRazonEmisor": self.company_id.name[0:120],
            "TipoFactura": verifactu_doc_type,
            "DescripcionOperacion": self._get_verifactu_description(),
            "Desglose": taxes_dict,
            "CuotaTotal": amount_tax,
            "ImporteTotal": amount_total,
            "Encadenamiento": self._get_verifactu_chaining_invoice_dict(),
            "SistemaInformatico": self._get_verifactu_developer_dict(),
            "FechaHoraHusoGenRegistro": self._get_verifactu_registration_date(),
            "TipoHuella": "01",  # SHA-256
            "Huella": self.verifactu_hash,
        }

        # Add rectification information for refunds
        if self._is_refund_order():
            inv_dict["TipoRectificativa"] = self.verifactu_refund_type
            # Add reference to original order if available
            if self.refunded_order_ids:
                original_order = self.refunded_order_ids[0]
                inv_dict["FacturasRectificadas"] = [
                    {
                        "IDFacturaRectificada": {
                            "IDEmisorFactura": original_order._get_verifactu_issuer(),
                            "NumSerieFactura": original_order._get_document_serial_number(),
                            "FechaExpedicionFactura": original_order._change_date_format(
                                original_order._get_document_date()
                            ),
                        }
                    }
                ]

        if self.aeat_state in ("sent_w_errors", "incorrect"):
            # en caso de subsanación, debe generar un nuevo hash
            inv_dict["Subsanacion"] = "S"
            if self.aeat_state == "incorrect":
                inv_dict["RechazoPrevio"] = "X"

        registroAlta = {}
        registroAlta.setdefault("RegistroAlta", inv_dict)
        return registroAlta

    def _get_verifactu_chaining_invoice_dict(self):
        """Get the chaining invoice dictionary for POS orders using the new system."""
        if (
            self.last_verifactu_invoice_entry_id
            and self.last_verifactu_invoice_entry_id.previous_invoice_entry_id
        ):
            prev_entry = self.last_verifactu_invoice_entry_id.previous_invoice_entry_id
            prev_document = prev_entry.document
            if prev_document:
                return {
                    "RegistroAnterior": {
                        "IDEmisorFactura": prev_document._get_verifactu_issuer(),
                        "NumSerieFactura": prev_document._get_document_serial_number(),
                        "FechaExpedicionFactura": prev_document._change_date_format(
                            prev_document._get_document_date()
                        ),
                        "Huella": self._get_verifactu_previous_hash(),
                    }
                }
        return {"PrimerRegistro": "S"}

    def _get_verifactu_receiver_dict(self):
        """Get receiver dict for POS orders."""
        self.ensure_one()
        partner = self._verifactu_get_partner()
        if not partner:
            return {}
        return {
            "NombreRazon": partner.name,
            "NIF": partner._parse_aeat_vat_info()[2] if partner.vat else "",
        }

    def _get_verifactu_taxes_and_total(self):
        """Get the tax breakdown for Verifactu from POS order lines.

        Returns:
            tuple: (taxes_dict, amount_tax, amount_total) where:
                - taxes_dict: Dictionary with tax breakdown
                - amount_tax: Total tax amount
                - amount_total: Total amount with taxes
        """
        self.ensure_one()
        taxes_dict = {}
        taxes_dict.setdefault("DetalleDesglose", [])

        # Get tax lines from POS order
        tax_lines = {}
        for line in self.lines:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_ids_after_fiscal_position.compute_all(
                price,
                self.pricelist_id.currency_id,
                line.qty,
                product=line.product_id,
                partner=self.partner_id or False,
            )

            for tax_vals in taxes["taxes"]:
                tax = self.env["account.tax"].browse(tax_vals["id"])
                if tax not in tax_lines:
                    tax_lines[tax] = {
                        "tax": tax,
                        "base": tax_vals["base"],
                        "amount": tax_vals["amount"],
                    }
                else:
                    tax_lines[tax]["base"] += tax_vals["base"]
                    tax_lines[tax]["amount"] += tax_vals["amount"]

        # Get tax mappings
        document_date = self._get_document_fiscal_date()
        taxes_S1 = self._get_verifactu_taxes_map(["S1"], document_date)
        taxes_S2 = self._get_verifactu_taxes_map(["S2"], document_date)
        taxes_N1 = self._get_verifactu_taxes_map(["N1"], document_date)
        taxes_N2 = self._get_verifactu_taxes_map(["N2"], document_date)
        taxes_RE = self._get_verifactu_taxes_map(["RE"], document_date)
        taxes_not_in_total = self._get_verifactu_taxes_map(
            ["TaxNotIncludedInTotal"], document_date
        )
        base_not_in_total = self._get_verifactu_taxes_map(
            ["BaseNotIncludedInTotal"], document_date
        )
        excluded_taxes = taxes_not_in_total + base_not_in_total
        breakdown_taxes = taxes_S1 + taxes_S2 + taxes_N1 + taxes_N2
        not_in_amount_total = 0.0
        not_in_taxes = 0.0

        # Build tax breakdown
        for tax_line in tax_lines.values():
            tax = tax_line["tax"]
            if tax in taxes_not_in_total:
                not_in_amount_total += tax_line["amount"]
            elif tax in base_not_in_total:
                not_in_amount_total += tax_line["base"]
            if tax in breakdown_taxes:
                operation_type = self._get_verifactu_operation_type(
                    tax_line, taxes_S1, taxes_S2, taxes_N1, taxes_N2
                )
                tax_dict = {
                    "Impuesto": self.verifactu_tax_key,
                    "ClaveRegimen": self.verifactu_registration_key_code,
                    "CalificacionOperacion": operation_type,
                }
                if operation_type not in ("N1", "N2"):
                    new_tax_dict = self._get_verifactu_tax_dict(tax_line, tax_lines)
                    tax_dict.update(new_tax_dict)
                else:
                    tax_dict.update({"BaseImponibleOimporteNoSujeto": tax_line["base"]})
                taxes_dict["DetalleDesglose"].append(tax_dict)
            elif tax in excluded_taxes:
                not_in_taxes += tax_line["amount"]
            elif tax not in taxes_RE:
                raise UserError(_("%s tax is not mapped to VERI*FACTU.", tax.name))
        sign = -1 if self._is_refund_order() else 1
        amount_tax = self.amount_tax - not_in_taxes * sign
        amount_total = self.amount_total - not_in_amount_total
        return (
            taxes_dict,
            amount_tax,
            amount_total,
        )

    def _get_verifactu_tax_dict(self, tax_line, tax_lines):
        """Get the Verifactu tax dictionary for the passed tax line.

        Args:
            tax_line (dict): Tax line being analyzed
            tax_lines (dict): Dictionary of processed taxes

        Returns:
            dict: Verifactu tax values
        """
        tax = tax_line["tax"]
        tax_base_amount = tax_line["base"]
        if tax.amount_type == "group":
            tax_type = abs(tax.children_tax_ids.filtered("amount")[:1].amount)
        else:
            tax_type = abs(tax.amount)

        tax_dict = {
            "TipoImpositivo": str(tax_type),
            "BaseImponibleOimporteNoSujeto": tax_base_amount,
            "CuotaRepercutida": tax_line["amount"],
        }

        # Recargo de equivalencia
        req_tax = self._get_verifactu_tax_req(tax)
        if req_tax:
            tax_dict["TipoRecargoEquivalencia"] = req_tax.amount
            tax_dict["CuotaRecargoEquivalencia"] = tax_lines[req_tax]["amount"]

        return tax_dict

    def _get_verifactu_tax_req(self, tax):
        """Get the associated req tax for the specified tax.

        Args:
            tax: Initial tax for searching RE linked tax

        Returns:
            account.tax: REQ tax linked to provided tax

        Raises:
            UserError: If there's a mismatch in RE taxes
        """
        self.ensure_one()
        document_date = self._get_document_fiscal_date()
        taxes_req = self._get_verifactu_taxes_map(["RE"], document_date)

        re_lines = self.lines.filtered(
            lambda x: tax in x.tax_ids and x.tax_ids & taxes_req
        )
        req_tax = re_lines.mapped("tax_ids") & taxes_req

        if len(req_tax) > 1:
            raise UserError(_("There's a mismatch in taxes for RE. Check them."))
        return req_tax

    def _get_verifactu_operation_type(
        self, tax_line, taxes_S1, taxes_S2, taxes_N1, taxes_N2
    ):
        """Get the operation type for Verifactu based on tax configuration.

        Args:
            tax_line (dict): Tax line info
            taxes_S1: Taxes for type S1
            taxes_S2: Taxes for type S2
            taxes_N1: Taxes for type N1
            taxes_N2: Taxes for type N2

        Returns:
            str: Operation type code (S1, S2, N1, N2)
        """
        tax = tax_line["tax"]
        if tax in taxes_S1:
            return "S1"
        elif tax in taxes_S2:
            return "S2"
        elif tax in taxes_N1:
            return "N1"
        elif tax in taxes_N2:
            return "N2"
        return "S1"

    @api.model
    def _cron_generate_pending_verifactu_chaining(self, limit=50, commit=False):
        """Chain the paid orders that were left out of the chain.

        Unlike backend invoices, a POS order cannot have its chaining failure
        surfaced to the user: the sale is already paid when it happens, so
        AccountMove._post() cannot be imitated (it lets the UserError abort the
        posting, which keeps the state consistent). This sweep is the recovery
        path that replaces it.

        No retry counter or backoff of its own is needed: the cron interval IS
        the backoff, and an order that loses the chaining lock simply shows up
        again on the next pass. The attempts counter only exists to stop
        retrying an order that can never be chained.
        """
        max_attempts = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_es_verifactu_pos_oca.max_chaining_attempts", 10)
        )
        # The domain replicates the computed field instead of searching by it:
        # its search method is laxer, and the orders it would let through come
        # back on every pass and, being the oldest, starve the rest.
        companies = (
            self.env["res.company"].sudo().search([("verifactu_enabled", "=", True)])
        )
        for company in companies:
            domain = [
                ("company_id", "=", company.id),
                ("to_invoice", "=", False),
                ("state", "in", VERIFACTU_VALID_POS_STATES),
                ("last_verifactu_invoice_entry_id", "=", False),
                ("verifactu_chaining_attempts", "<", max_attempts),
                ("session_id.config_id.journal_id.verifactu_enabled", "=", True),
                # Last leg of the computed field, easy to miss.
                "|",
                ("fiscal_position_id", "=", False),
                ("fiscal_position_id.aeat_active", "=", True),
            ]
            if company.verifactu_start_date:
                domain.append(
                    (
                        "date_order",
                        ">=",
                        fields.Date.to_string(company.verifactu_start_date),
                    )
                )
            orders = self.search(
                domain,
                # Oldest first: the position in the chain is today's, but the
                # pending orders enter it in the order they were charged.
                order="date_order ASC",
                limit=limit,
            )
            for order in orders:
                try:
                    with self.env.cr.savepoint():
                        order._recover_verifactu_chaining()
                except Exception as error:  # noqa: BLE001 -- see below
                    # Isolated per order: unhandled, this would reach the
                    # cron runner and roll back the whole pass. Only the id is
                    # logged -- any other field goes back to a row that just
                    # failed.
                    _logger.exception(
                        "[ID: %d] VERI*FACTU chaining recovery raised an "
                        "unexpected error",
                        order.id,
                    )
                    self._record_recovery_failure(order, error)
                # The chaining lock is held until the transaction commits, so
                # committing per order is what keeps the sweep from blocking
                # the tills. Off by default: only the scheduled action opts in.
                if commit:  # pragma: no cover
                    self.env.cr.commit()  # pylint: disable=invalid-commit
        return True

    def _record_recovery_failure(self, order, error):
        """Leave a trace of a failure the recovery could not handle itself.

        Concurrency errors get none on purpose: they are transient, and the
        write would land on the row that just failed and fail the same way.
        """
        if (
            isinstance(error, psycopg2.OperationalError)
            and error.pgcode in PG_CONCURRENCY_ERRORS_TO_RETRY
        ):
            return
        try:
            with self.env.cr.savepoint():
                order._mark_verifactu_chaining_failure(error)
        except Exception:  # noqa: BLE001
            _logger.exception(
                "[ID: %d] Could not record the VERI*FACTU chaining failure",
                order.id,
            )

    def _recover_verifactu_chaining(self):
        """Chain an order that has no entry yet. Idempotent by state."""
        self.ensure_one()
        # Idempotence lives here, not in an identity key: if the normal flow or
        # a previous pass already chained this order, a second link would be a
        # second registration of the same sale.
        if self.last_verifactu_invoice_entry_id:
            return False
        # Re-validate: the order may have changed state between the failure and
        # this retry.
        if not self._is_verifactu_order():
            return False
        try:
            # _check_verifactu_configuration() is deliberately not called:
            # recovery reproduces the normal chaining path, which does not call
            # it either. The override here demands a fiscal position, which a
            # counter sale does not have.
            self.verifactu_registration_date = fields.Datetime.now()
            self._generate_verifactu_chaining()
        except UserError as e:
            _logger.error(
                "[ID: %d, REF: %s] VERI*FACTU chaining recovery failed: %s",
                self.id,
                self.pos_reference,
                str(e),
            )
            self._mark_verifactu_chaining_failure(
                e, spend_attempt=not isinstance(e, VerifactuChainingLocked)
            )
            return False
        self.write({"aeat_send_failed": False, "aeat_send_error": False})
        return True

    def action_recover_verifactu_chaining(self):
        """Manual counterpart of the recovery cron, for a single order."""
        self.ensure_one()
        if self._recover_verifactu_chaining():
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("VERI*FACTU chaining generated"),
                    "message": _("The order has been added to the chain."),
                    "type": "success",
                },
            }
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("VERI*FACTU chaining not generated"),
                "message": self.aeat_send_error
                or _("The order is not eligible for chaining."),
                "type": "warning",
            },
        }

    def resend_verifactu(self):
        """Resend POS orders to verifactu after errors"""
        for order in self:
            if (
                order.aeat_state in ("sent_w_errors", "incorrect")
                and order.last_verifactu_invoice_entry_id
                and not order.last_verifactu_invoice_entry_id.send_state == "not_sent"
            ):
                entry_type = (
                    "modify" if order.aeat_state == "sent_w_errors" else "register"
                )
                order.verifactu_registration_date = fields.Datetime.now()
                order._generate_verifactu_chaining(entry_type=entry_type)

    def _check_verifactu_configuration(self):
        """Check POS order configuration for verifactu"""
        if not self.fiscal_position_id:
            raise UserError(
                _(
                    "[ID: %(id)d, REF: %(ref)s, INV: %(inv)s] The POS order cannot be sent to "
                    "Verifactu because it does not have a fiscal position."
                )
                % {
                    "id": self.id,
                    "ref": self.pos_reference,
                    "inv": self.l10n_es_unique_id,
                }
            )
        if not self.verifactu_tax_key:
            raise UserError(
                _(
                    "[ID: %(id)d, REF: %(ref)s, INV: %(inv)s] The POS order cannot be sent to "
                    "Verifactu because it does not have a tax key."
                )
                % {
                    "id": self.id,
                    "ref": self.pos_reference,
                    "inv": self.l10n_es_unique_id,
                }
            )
        if not self.verifactu_registration_key:
            raise UserError(
                _(
                    "[ID: %(id)d, REF: %(ref)s, INV: %(inv)s] The POS order cannot be sent to "
                    "Verifactu because it does not have a registration key."
                )
                % {
                    "id": self.id,
                    "ref": self.pos_reference,
                    "inv": self.l10n_es_unique_id,
                }
            )

        if not self._check_inconsistent_taxes():
            raise UserError(
                _(
                    "[ID: %(id)d, REF: %(ref)s, INV: %(inv)s] The POS order cannot be sent to "
                    "Verifactu because there are some inconsistent taxes on lines."
                )
                % {
                    "id": self.id,
                    "ref": self.pos_reference,
                    "inv": self.l10n_es_unique_id,
                }
            )

        if not self._check_all_taxes_mapped():
            raise UserError(
                _(
                    "[ID: %(id)d, REF: %(ref)s, INV: %(inv)s] The POS order cannot be sent to "
                    "Verifactu because it does not have all taxes mapped."
                )
                % {
                    "id": self.id,
                    "ref": self.pos_reference,
                    "inv": self.l10n_es_unique_id,
                }
            )
        return super()._check_verifactu_configuration()

    def _check_inconsistent_taxes(self):
        """Check for inconsistent taxes on POS order lines"""
        document_date = self._get_document_fiscal_date()
        taxes_S1 = self._get_verifactu_taxes_map(["S1"], document_date)
        taxes_S2 = self._get_verifactu_taxes_map(["S2"], document_date)
        taxes_RE = self._get_verifactu_taxes_map(["RE"], document_date)

        for line in self.lines:
            taxes_in_s1 = line.tax_ids_after_fiscal_position.filtered(
                lambda x: x in taxes_S1
            )
            if len(taxes_in_s1) > 1:
                return False
            taxes_in_s2 = line.tax_ids_after_fiscal_position.filtered(
                lambda x: x in taxes_S2
            )
            if len(taxes_in_s2) > 1:
                return False
            taxes_in_RE = line.tax_ids_after_fiscal_position.filtered(
                lambda x: x in taxes_RE
            )
            if len(taxes_in_RE) > 1:
                return False
        return True

    def _check_all_taxes_mapped(self):
        """Check if all taxes used in POS order are mapped to verifactu"""
        # Get all taxes used in the order
        all_taxes = self.env["account.tax"]
        for line in self.lines:
            all_taxes |= line.tax_ids_after_fiscal_position

        if not all_taxes:
            raise UserError(
                _(
                    "The POS order %s cannot be sent to Verifactu because"
                    "it does not have any taxes."
                )
                % self.pos_reference
            )

        document_date = self._get_document_fiscal_date()
        verifactu_map = self._get_verifactu_map(document_date)
        tax_templates = verifactu_map.map_lines.mapped("taxes")
        mapped_taxes = self.company_id.get_taxes_from_templates(tax_templates)

        for tax in all_taxes:
            if tax not in mapped_taxes:
                return False
        return True

    def cancel_verifactu(self):
        """Cancel POS order on verifactu - not implemented"""
        raise NotImplementedError

    def write(self, vals):
        """Override write to protect fields once sent to verifactu"""
        PROTECTED_FIELDS = {
            "date_order": _("order date"),
            "pos_reference": _("POS reference"),
            "l10n_es_unique_id": _("simplified invoice number"),
        }

        modified_protected = set(vals.keys()) & set(PROTECTED_FIELDS.keys())
        if modified_protected:
            for order in self.filtered(
                lambda x: x.verifactu_enabled and x.aeat_state != "not_sent"
            ):
                protected_field_names = [
                    PROTECTED_FIELDS[field] for field in modified_protected
                ]
                raise UserError(
                    _(
                        "[ID: %(id)d, REF: %(ref)s, INV: %(inv)s] "
                        "You cannot change the %(fields)s "
                        "of document already registered at VERI*FACTU. You must cancel the "
                        "document and create a new one with the correct value."
                    )
                    % {
                        "id": order.id,
                        "ref": order.pos_reference,
                        "inv": order.l10n_es_unique_id,
                        "fields": ", ".join(protected_field_names),
                    }
                )

        return super().write(vals)
