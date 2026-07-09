Before using the report, make sure that the taxes and products of
`l10n_es_digital_canon` are configured and loaded.

Example workflow for generating a common report line:

1. Create a purchase order with a Spanish vendor.
2. Assign a product that has a digital canon category.
3. Confirm the purchase order.
4. Confirm the related incoming picking, assigning a lot to the product.
5. Create and post the vendor bill.
6. Go to Sales and create a sales order with the same product.
7. Confirm the sales order.
8. Confirm the related outgoing picking, assigning the same lot.
9. Create and post the customer invoice from the sales order.

After these steps, go to **Invoicing > Reports > SGAE**, click on the
**Digital Canon** menu, and set the desired dates (normally quarterly).
This will generate the XLSX report ready to be submitted, with all fields
completed according to the purchase and sales conditions.
