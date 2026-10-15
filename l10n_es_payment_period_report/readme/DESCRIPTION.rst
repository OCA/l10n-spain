This module computes the average payment period to suppliers that Spanish
companies disclose in the notes of their annual accounts (additional provision
three of Law 15/2010, ICAC Resolution of 29 January 2016 and Law 18/2022).

Two methods are available in the wizard, and only the selected one is computed:

* **Normal annual accounts** (ICAC Resolution, article 5.1 to 5.4):

  * Ratio of paid operations: each payment made in the period is weighted by
    the days from the invoice start date to the payment date. An invoice paid
    in instalments contributes each instalment with its own days.
  * Ratio of operations pending payment: the amount still unpaid at the end of
    the period, rebuilt from the reconciliations done up to that date, is
    weighted by the days from the invoice start date to the end of the period.
  * Average payment period: weighted average of both ratios, with the total
    payments made and pending.
  * Law 18/2022 figures: monetary volume and number of invoices paid within the
    legal payment period, and their percentages. An invoice counts as paid
    within the legal period when every payment it received in the period was.

* **Abbreviated annual accounts or SME** (article 5.5): average trade creditors
  balance (opening and closing) divided by net purchases plus external
  services, multiplied by 365.

The normal method takes posted supplier invoices and receipts on payable
accounts. Only payments count as such: credit notes, other invoices and
exchange differences reconciled with an invoice reduce its amount instead.

The abbreviated method reads the Spanish chart of accounts: suppliers
(400, 401, 403, 404, 405, 406) and sundry creditors (41) for the trade
creditors balance, subgroup 60 for net purchases and subgroup 62 for external
services.
