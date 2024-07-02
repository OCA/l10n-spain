# Part of Odoo. See LICENSE file for full copyright and licensing details.

# List of ISO 15897 locale supported by Mollie
# See full details at `locale` parameter at https://docs.mollie.com/reference/v2/payments-api/create-payment
SUPPORTED_LOCALES = [
    'fr_FR', 'es_ES', 'pt_PT', 'it_IT'
]

# Currency codes in ISO 4217 format supported by mollie.
# Note: support varies per payment method.
# See https://docs.mollie.com/payments/multicurrency. Last seen online: 22 September 2022.
SUPPORTED_CURRENCIES = [
    'EUR'
]

# The codes of the payment methods to activate when Mollie is activated.
DEFAULT_PAYMENT_METHODS_CODES = [
    # Primary payment methods.
    'pp3',
]

# Mapping of payment method codes to Mollie codes.
PAYMENT_METHODS_MAPPING = {
    'apple_pay': 'applepay',
    'card': 'creditcard',
    'bank_transfer': 'banktransfer',
    'p24': 'przelewy24',
    'sepa_direct_debit': 'directdebit',
}