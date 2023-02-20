11.0.2.1.0 (2023-02-20)
~~~~~~~~~~~~~~~~~~~~~~~

* Backport [[13.0][FIX] l10n_es: Includes new food taxes reduction](https://github.com/odoo/odoo/pull/108868)

Se mantiene el uso de los impuestos de alimentos en v11.

En posteriores versiones se renombran de la siguiente manera:

.. code-block:: xml

    ("account_tax_template_p_iva0_a", "account_tax_template_p_iva0_s_bc")
    ("account_tax_template_p_iva5_a", "account_tax_template_p_iva5_bc")
    ("account_tax_template_p_iva0_ic_a", "account_tax_template_p_iva0_ic_bc")
    ("account_tax_template_p_iva5_ic_a", "account_tax_template_p_iva5_ic_bc")
    ("account_tax_template_p_iva0_ia", "account_tax_template_p_iva0_ibc")
    ("account_tax_template_p_iva5_ia", "account_tax_template_p_iva5_ibc")
    ("account_tax_template_p_req0625", "account_tax_template_p_req062")
    ("account_tax_template_s_iva0_a", "account_tax_template_s_iva0b")
    ("account_tax_template_s_iva5_a", "account_tax_template_s_iva5b")
    ("account_tax_template_s_req0625", "account_tax_template_s_req062")

11.0.1.0.0 (2022-08-10)
~~~~~~~~~~~~~~~~~~~~~~~

* [NEW] Module backported to v11. Añadido nuevo impuesto del 5% de las eléctricas.
