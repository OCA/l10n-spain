Para instalar este modulo necesitas:

* account
* base_vat
* l10n_es
* l10n_es_aeat

Se instalan automáticamente si están disponibles en la lista de addons.

Consideraciones adicionales:

* Es importante que en facturas que deban aparecer en los libros registros,
  no sujetos a IVA, informar el tipo de IVA 'No Sujeto' en facturas. Para
  evitar que los usuarios olviden informarlo es recomendable instalar el
  módulo 'account_invoice_tax_required', disponible en
  `account_invoice_tax_required <https://github.com/OCA/account-financial-
  tools/tree/11.0>`_.

* Actualmente, solo está creado el impuesto no deducible P_IVA0_ND en
  impuestos, que corresponde al 21%. Para que funcionen correctamente los
  nuevos mapeos, se deben crear antes de la instalación del módulo, o
  configurarlo manualmente luego, los impuestos no deducibles P_IVA10_ND
  (10% no deducible) y P_IVA4_ND (4% no deducible) en impuestos.

* En el nuevo libro de IVA es obligatorio declarar el IVA deducible y no
  deducible en facturas recibidas. Se añaden nuevos mapeos para los impuestos
  no deducibles.
