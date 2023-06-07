##############################################################################
#
# Copyright (c) 2023 Binhex System Solutions
# Copyright (c) 2023 Nicolás Ramos (http://binhex.es)
#
# The licence is in the file __manifest__.py
##############################################################################

from odoo import exceptions

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)


# Tests that a new instance of the class can be created with valid parameters.
def test_creating_instance_with_valid_parameters(self):
    # Arrange
    report = self.env["l10n.es.atc.mod420.report"].create({
        "name": "Test Report",
        "company_id": self.env.ref("base.main_company").id,
        "date_from": "2022-01-01",
        "date_to": "2022-03-31",
    })

    # Act
    result = report.name

    # Assert
    assert result == "Test Report"

# Tests that the total accrued and deductible installments are computed correctly.
def test_compute_total_installments(self):
    # Arrange
    report = self.env["l10n.es.atc.mod420.report"].create({
        "name": "Test Report",
        "company_id": self.env.ref("base.main_company").id,
        "date_from": "2022-01-01",
        "date_to": "2022-03-31",
    })
    tax_line_1 = self.env["l10n.es.aeat.tax.line"].create({
        "report_line_id": report.id,
        "field_number": 3,
        "amount": 100.0,
    })
    tax_line_2 = self.env["l10n.es.aeat.tax.line"].create({
        "report_line_id": report.id,
        "field_number": 6,
        "amount": 50.0,
    })

    # Act
    report._compute_total_devengado()
    report._compute_total_deducir()
    result_devengado = report.total_devengado
    result_deducir = report.total_deducir

    # Assert
    assert result_devengado == 150.0
    assert result_deducir == 0.0

# Tests that the result type is computed correctly for negative results in different period types.
def test_negative_result(self):
    # Arrange
    report = self.env["l10n.es.atc.mod420.report"].create({
        "name": "Test Report",
        "company_id": self.env.ref("base.main_company").id,
        "date_from": "2022-01-01",
        "date_to": "2022-12-31",
        "period_type": "12",
    })
    report.resultado_autoliquidacion = -100.0

    # Act
    report._compute_result_type()
    result = report.result_type

    # Assert
    assert result == "D"

# Tests that the difference between the total accrued and deductible installments is computed correctly.
def test_compute_difference(self):
    # Arrange
    report = self.env["l10n.es.atc.mod420.report"].create({
        "name": "Test Report",
        "company_id": self.env.ref("base.main_company").id,
        "date_from": "2022-01-01",
        "date_to": "2022-03-31",
    })
    tax_line_1 = self.env["l10n.es.aeat.tax.line"].create({
        "report_line_id": report.id,
        "field_number": 3,
        "amount": 100.0,
    })
    tax_line_2 = self.env["l10n.es.aeat.tax.line"].create({
        "report_line_id": report.id,
        "field_number": 27,
        "amount": 50.0,
    })

    # Act
    report._compute_total_devengado()
    report._compute_total_deducir()
    report._compute_diferencia()
    result = report.diferencia

    # Assert
    assert result == 50.0

# Tests that the self-assessment result is computed correctly.
def test_compute_self_assessment_result(self):
    # Arrange
    report = self.env["l10n.es.atc.mod420.report"].create({
        "name": "Test Report",
        "company_id": self.env.ref("base.main_company").id,
        "date_from": "2022-01-01",
        "date_to": "2022-03-31",
    })
    report.total_devengado = 100.0
    report.total_deducir = 50.0
    report.regularizacion_cuotas = 10.0
    report.cuotas_compensar = 20.0
    report.a_deducir = 5.0

    # Act
    report._compute_resultado_autoliquidacion()
    result = report.resultado_autoliquidacion

    # Assert
    assert result == 35.0

# Tests that the report can be confirmed without errors.
def test_confirm_report(self):
    # Arrange
    report = self.env["l10n.es.atc.mod420.report"].create({
        "name": "Test Report",
        "company_id": self.env.ref("base.main_company").id,
        "date_from": "2022-01-01",
        "date_to": "2022-03-31",
    })

    # Act
    result = report.button_confirm()

    # Assert
    assert result == True

# Tests that the result type is computed correctly for zero result.
def test_result_type_zero_result(self):
    report = self.env["l10n.es.atc.mod420.report"].create({})
    report.resultado_autoliquidacion = 0
    report._compute_result_type()
    assert report.result_type == "N"

# Tests that the bank account selection is checked when the result type is "I" or "D".
def test_bank_account_selection(self):
    report = self.env["l10n.es.atc.mod420.report"].create({})
    report.result_type = "I"
    with pytest.raises(Exception):
        report.button_confirm()
    report.bank_account_id = self.env["res.partner.bank"].create({"acc_number": "1234567890"})
    assert report.button_confirm() == True

# Tests that the default counterpart account is set to an account with code like "4757%".
def test_default_counterpart_account(self, mocker):
    account = self.env["account.account"].create({"code": "475700"})
    mocker.patch("odoo.models.Model.env")
    Model.env.return_value = self.env
    report = self.env["l10n.es.atc.mod420.report"].create({})
    assert report.counterpart_account_id == account