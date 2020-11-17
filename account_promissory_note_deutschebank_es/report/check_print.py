from odoo import models


class ReportPromissoryNotePrintDBES(models.AbstractModel):
    # The definition of this abstract model is done because is needed by
    # account_check_printing_report_base for the report to work.
    _name = 'report.account_promissory_note_deutschebank_es.promissory_db'
    _inherit = 'report.account_check_printing_report_base.promissory_footer_a4'
