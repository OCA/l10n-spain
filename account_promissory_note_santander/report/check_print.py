from odoo import models


class ReportPromissoryNotePrintCB(models.AbstractModel):
    # The definition of this abstract model is done because is needed by
    # account_check_printing_report_base for the report to work.
    _name = 'report.account_promissory_note_santander.promissory_footer_st'
    _inherit = 'report.account_check_printing_report_base.promissory_footer_a4'
