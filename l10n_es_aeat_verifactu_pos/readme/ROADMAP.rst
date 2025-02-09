* Refactor `retry` strategy when database is locked trying to obtain the last verifactu invoice from PoS config
* Implement stopping mechanism to avoid sending more invoices to the AEAT when there is a problem with the chain
* Implement cancelling simplified and complete invoices from the PoS
* Multiple devices per PoS Config (l10n_es_pos_by_device)
* Invoicing already sent simplified invoice (PoS Order). Send anullment for the simplified and send a new one for the complete.
