# Copyright 2023 Factor Libre S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    cr.execute(
        """
        UPDATE
            queue_job
        SET
            method_name = REPLACE(method_name, 'confirm_one_invoice', 'confirm_one_document'),
            name = REPLACE(name, 'confirm_one_invoice', 'confirm_one_document'),
            func_string = REPLACE(func_string, 'confirm_one_invoice', 'confirm_one_document')
        WHERE
            method_name = 'confirm_one_invoice' AND
            state in ('wait_dependencies', 'pending', 'enqueued')
        """
    )
