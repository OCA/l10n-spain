This module adds the Spanish bank entity code to bank accounts. Odoo 20.0 removed banks
(`res.bank`) and keeps the bank details on each account, so the code is taken from the
account number when it is a valid Spanish IBAN.

The code is stored, so bank accounts can be searched, filtered and grouped by it, and
other modules can use it, such as the bank code of Facturae invoices.
