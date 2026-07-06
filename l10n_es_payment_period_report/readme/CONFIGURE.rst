The ICAC Resolution leaves fixed asset suppliers and finance lease creditors
out of the scope. The normal method takes every payable account, so keep those
creditors on accounts that are not of type payable, or extend
``_l10n_es_payment_period_report_invoice_line_domain`` to exclude them.

For the abbreviated method, the account code prefixes are returned by
``_l10n_es_payment_period_report_account_prefixes`` and can be extended for
charts of accounts with other codes. Trade creditors balances include VAT
while purchases and external services do not; the Resolution does not set any
adjustment, so the figures are taken as they are booked.
