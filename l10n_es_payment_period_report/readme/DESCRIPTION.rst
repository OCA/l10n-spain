This module provides a supplier payment period report for Spanish companies.

It calculates the information needed for the supplier payment disclosure derived
from Law 15/2010 and Law 18/2022:

* Total amount paid.
* Amount paid within the configured legal payment period.
* Number of paid supplier invoices.
* Number of paid supplier invoices within the configured legal payment period.
* The corresponding percentages.

The computation is based on payable journal item reconciliations
(``account.partial.reconcile``). The payment date is the last reconciliation
date that completes the supplier invoice cancellation.
