# Copyright 2016-2017 Tecnativa - Pedro M. Baeza
# Copyright 2017 Tecnativa - Carlos Dauden <carlos.dauden@tecnativa.com>
# Copyright 2026 Studio73 - Pablo Cortés <pablo.cortes@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import csv
import importlib.util
from pathlib import Path
from unittest.mock import patch

import requests

from odoo.exceptions import AccessError
from odoo.tests.common import new_test_user
from odoo.tools import mute_logger

from .common import L10nEsPartnerCommon


class TestPartnerSearchAndDisplay(L10nEsPartnerCommon):
    def test_01_search_by_partner_and_commercial_name(self):
        partner_model = self.env["res.partner"]
        standard_name_ids = [
            partner[0] for partner in partner_model.name_search("prueba")
        ]
        commercial_name_ids = [
            partner[0] for partner in partner_model.name_search("comercial")
        ]
        self.assertIn(self.partner.id, standard_name_ids)
        self.assertNotIn(
            self.partner.id,
            [
                partner[0]
                for partner in partner_model.name_search("prueba", operator="not ilike")
            ],
        )
        self.assertIn(self.partner.id, commercial_name_ids)
        self.assertNotIn(
            self.partner.id,
            [
                partner[0]
                for partner in partner_model.name_search(
                    "comercial", operator="not ilike"
                )
            ],
        )

    def test_02_name_pattern_formats_address_and_complete_name(self):
        self.env["ir.config_parameter"].sudo().set_str(
            "l10n_es_partner.name_pattern", "%(comercial_name)s (%(name)s)"
        )
        partner = (
            self.env["res.partner"]
            .sudo()
            .create(
                {
                    "name": "Empresa de prueba",
                    "comercial": "Nombre comercial",
                    "street": "My street",
                }
            )
        )
        expected_name = "Nombre comercial (Empresa de prueba)"
        self.assertEqual(partner.display_name, expected_name)
        self.assertEqual(partner.complete_name, expected_name)
        self.assertEqual(
            partner.with_context(show_address=True).display_name,
            f"{expected_name}\nMy street",
        )

    def test_03_context_hides_commercial_name(self):
        self.env["ir.config_parameter"].sudo().set_str(
            "l10n_es_partner.name_pattern", "%(comercial_name)s (%(name)s)"
        )
        partner = (
            self.env["res.partner"]
            .sudo()
            .create({"name": "Empresa de prueba", "comercial": "Nombre comercial"})
        )
        self.assertEqual(
            partner.with_context(no_display_commercial=True).display_name,
            "Empresa de prueba",
        )


class TestBankImport(L10nEsPartnerCommon):
    @staticmethod
    def _write_import_csv(destination, code):
        fieldnames = [
            "id",
            "name",
            "lname",
            "code",
            "bic",
            "street",
            "street2",
            "website",
            "vat",
            "city",
            "zip",
            "phone",
            "active",
            "state:id",
            "country:id",
        ]
        values = [
            f"res_bank_es_{code}",
            "Test Bank",
            "Test Bank Long Name",
            code,
            "TESTESMMXXX",
            "Test Street",
            "",
            "https://example.test",
            "A12345678",
            "Madrid",
            "28001",
            "910000000",
            "1",
            "base.state_es_m",
            "base.es",
        ]
        with open(destination, "w", encoding="utf-8", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(fieldnames)
            writer.writerow(values)

    def _admin_wizard(self):
        return (
            self.env["l10n.es.partner.import.wizard"].with_user(self.admin).create({})
        )

    def test_01_local_import_is_repeatable(self):
        wizard = self._admin_wizard()
        wizard.import_local()
        wizard.import_local()

        banks = self.env["l10n.es.bank"].search([("code", "=", "0182")])
        self.assertEqual(len(banks), 1)
        self.assertEqual(banks.name, "Bbva")
        self.assertEqual(self.env.ref("l10n_es_partner.res_bank_es_0182"), banks)

    def test_02_download_import_uses_converted_file(self):
        wizard = self._admin_wizard()
        response = type(
            "Response",
            (),
            {"content": b"xls", "raise_for_status": staticmethod(lambda: None)},
        )()
        module_path = "odoo.addons.l10n_es_partner.wizard.l10n_es_partner_wizard"
        with (
            patch("requests.get", return_value=response) as mocked_get,
            patch.object(type(wizard), "_xls_to_csv", return_value=True),
            patch(
                f"{module_path}.gen_bank_data_csv",
                side_effect=lambda _source, destination: self._write_import_csv(
                    destination, "9999"
                ),
            ),
        ):
            wizard.execute()

        mocked_get.assert_called_once_with(
            "https://www.bde.es/f/webbde/SGE/regis/REGBANESP_CONESTAB_A.xls",
            timeout=15,
        )
        self.assertTrue(self.env["l10n.es.bank"].search([("code", "=", "9999")]))

    def test_03_download_failure_imports_local_backup(self):
        wizard = self._admin_wizard()
        module_path = "odoo.addons.l10n_es_partner.wizard.l10n_es_partner_wizard"
        with (
            mute_logger("odoo.addons.l10n_es_partner.wizard.l10n_es_partner_wizard"),
            patch("requests.get", side_effect=requests.ConnectionError),
            patch(
                f"{module_path}.gen_bank_data_csv",
                side_effect=lambda source, destination: self._write_import_csv(
                    destination, "9998"
                ),
            ) as mocked_generator,
        ):
            wizard.execute()

        self.assertTrue(
            mocked_generator.call_args.args[0].endswith(
                "l10n_es_partner/gen_src/REGBANESP_CONESTAB_A.csv"
            )
        )
        self.assertTrue(self.env["l10n.es.bank"].search([("code", "=", "9998")]))

    def test_04_catalog_permissions_match_bank_roles(self):
        catalog = self.env["l10n.es.bank"]
        self.assertEqual(catalog.search_count([]), 0)
        with self.assertRaises(AccessError):
            catalog.create({"name": "No access"})

        manager = new_test_user(
            self.env,
            name="Bank Catalog Manager",
            login="bank_catalog_manager",
            password="test",
            email="bank_catalog_manager@example.test",
            group_ids=[
                self.env.ref("base.group_user").id,
                self.env.ref("base.group_partner_manager").id,
            ],
        )
        manager_catalog = catalog.with_user(manager)
        bank = manager_catalog.create({"name": "Manager bank", "code": "9988"})
        bank.write({"name": "Manager bank updated"})
        self.assertEqual(bank.name, "Manager bank updated")


class TestBankAccountCatalogLink(L10nEsPartnerCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.bank = (
            cls.env["l10n.es.bank"]
            .sudo()
            .create(
                {
                    "name": "BBVA Catalog",
                    "lname": "Banco Bilbao Vizcaya Argentaria",
                    "code": "0182",
                    "bic": "BBVAESMMXXX",
                    "street": "Catalog Street",
                    "city": "Bilbao",
                    "zip": "48005",
                    "state_id": cls.env.ref("base.state_es_bi").id,
                    "country_id": cls.spain.id,
                }
            )
        )
        cls.iban = "ES9101820000000000000000"

    def test_01_valid_spanish_iban_links_catalog(self):
        account = (
            self.env["res.partner.bank"]
            .with_user(self.admin)
            .create({"partner_id": self.partner.id, "account_number": self.iban})
        )
        self.assertEqual(account.l10n_es_bank_id, self.bank)
        self.assertEqual(account.bank_name, self.bank.name)
        self.assertEqual(account.bank_bic, self.bank.bic)
        self.assertEqual(account.street, self.bank.street)
        self.assertEqual(account.country_id, self.spain)

    def test_02_iban_preserves_explicit_account_values(self):
        account = (
            self.env["res.partner.bank"]
            .with_user(self.admin)
            .create(
                {
                    "partner_id": self.partner.id,
                    "account_number": self.iban,
                    "bank_name": "Manual Bank Name",
                    "bank_bic": "MANUALESXXX",
                    "street": "Manual Street",
                }
            )
        )
        self.assertEqual(account.l10n_es_bank_id, self.bank)
        self.assertEqual(account.bank_name, "Manual Bank Name")
        self.assertEqual(account.bank_bic, "MANUALESXXX")
        self.assertEqual(account.street, "Manual Street")

    def test_03_manual_bank_selection_fills_blank_account_details(self):
        account_model = self.env["res.partner.bank"].with_user(self.admin)
        account = account_model.create(
            {
                "partner_id": self.partner.id,
                "account_number": "1234567890",
                "l10n_es_bank_id": self.bank.id,
            }
        )
        self.assertEqual(account.bank_name, self.bank.name)
        self.assertEqual(account.bank_bic, self.bank.bic)
        self.assertEqual(account.street, self.bank.street)

        onchange_account = account_model.new({"l10n_es_bank_id": self.bank.id})
        onchange_account._onchange_l10n_es_bank_id()
        self.assertEqual(onchange_account.bank_name, self.bank.name)
        self.assertEqual(onchange_account.city, self.bank.city)


class TestBankMigration(L10nEsPartnerCommon):
    @staticmethod
    def _load_migration_script(script_name):
        module_path = Path(__file__).resolve().parents[1]
        script_path = module_path / "migrations" / "20.0.1.0.0" / script_name
        spec = importlib.util.spec_from_file_location(script_name, script_path)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        return migration

    def test_01_pre_upgrade_snapshot_is_reusable(self):
        cr = self.env.cr
        cr.execute("CREATE TABLE res_bank (id integer, name varchar, code varchar)")
        cr.execute(
            "INSERT INTO res_bank (id, name, code) VALUES (990001, 'Old bank', '9900')"
        )
        cr.execute("ALTER TABLE res_partner_bank ADD COLUMN bank_id integer")
        account = (
            self.env["res.partner.bank"]
            .sudo()
            .create({"partner_id": self.partner.id, "account_number": "migration-test"})
        )
        cr.execute(
            "UPDATE res_partner_bank SET bank_id = 990001 WHERE id = %s",
            (account.id,),
        )
        cr.execute(
            """
            INSERT INTO ir_model_data (module, name, model, res_id, noupdate)
            VALUES ('l10n_es_partner', 'bank_preupgrade_test', 'res.bank', 990001, TRUE)
            """
        )
        migration = self._load_migration_script("pre-migration.py")

        migration.migrate(cr, "19.0.1.0.3")
        migration.migrate(cr, "19.0.1.0.3")

        cr.execute("SELECT COUNT(*) FROM l10n_es_partner_pre20_res_bank")
        self.assertEqual(cr.fetchone()[0], 1)
        cr.execute("SELECT COUNT(*) FROM l10n_es_partner_pre20_res_bank_xmlids")
        self.assertEqual(cr.fetchone()[0], 1)
        cr.execute("SELECT id, bank_id FROM l10n_es_partner_pre20_bank_accounts")
        self.assertEqual(cr.fetchone(), (account.id, 990001))

    def test_02_post_upgrade_restores_catalog_xmlids_links_and_manual_values(self):
        cr = self.env.cr
        cr.execute("ALTER TABLE l10n_es_bank ADD COLUMN x_catalog_ref varchar")
        account = (
            self.env["res.partner.bank"]
            .sudo()
            .create(
                {
                    "partner_id": self.partner.id,
                    "account_number": "migration-restore-test",
                    "bank_name": "Manual account name",
                    "bank_bic": "MANUALBIC",
                    "street": "Manual account street",
                }
            )
        )
        cr.execute("SELECT nextval(pg_get_serial_sequence('l10n_es_bank', 'id'))")
        bank_id = cr.fetchone()[0]
        cr.execute(
            """
            CREATE TABLE l10n_es_partner_pre20_res_bank (
                id integer, name varchar, lname varchar, code varchar, bic varchar,
                street varchar, street2 varchar, zip varchar, city varchar,
                state integer, country integer, email varchar, phone varchar,
                active boolean, vat varchar, website varchar, x_catalog_ref varchar
            )
            """
        )
        cr.execute(
            """
            INSERT INTO l10n_es_partner_pre20_res_bank
                (id, name, lname, code, bic, street, city, zip, state, country,
                 email, phone, active, vat, website, x_catalog_ref)
            VALUES (%s, 'Restored bank', 'Restored long name', '9876',
                    'RESTESMMXXX', 'Restored street', 'Madrid', '28001',
                    %s, %s, 'bank@example.test', '910000000', FALSE,
                    'A12345678', 'https://example.test', 'customer-specific')
            """,
            (bank_id, self.env.ref("base.state_es_m").id, self.spain.id),
        )
        cr.execute(
            """
            CREATE TABLE l10n_es_partner_pre20_res_bank_xmlids (
                module varchar, name varchar, model varchar, res_id integer,
                noupdate boolean
            )
            """
        )
        cr.execute(
            """
            INSERT INTO l10n_es_partner_pre20_res_bank_xmlids
                (module, name, model, res_id, noupdate)
            VALUES ('l10n_es_partner', 'migration_restored_bank', 'res.bank', %s, TRUE)
            """,
            (bank_id,),
        )
        cr.execute(
            "CREATE TABLE l10n_es_partner_pre20_bank_accounts "
            "(id integer, bank_id integer)"
        )
        cr.execute(
            "INSERT INTO l10n_es_partner_pre20_bank_accounts VALUES (%s, %s)",
            (account.id, bank_id),
        )

        migration = self._load_migration_script("post-migration.py")
        migration.migrate(cr, "19.0.1.0.3")

        restored_bank = self.env["l10n.es.bank"].sudo().browse(bank_id)
        account.invalidate_recordset()
        self.assertEqual(restored_bank.name, "Restored bank")
        self.assertEqual(restored_bank.lname, "Restored long name")
        self.assertEqual(restored_bank.code, "9876")
        self.assertFalse(restored_bank.active)
        cr.execute("SELECT x_catalog_ref FROM l10n_es_bank WHERE id = %s", (bank_id,))
        self.assertEqual(cr.fetchone()[0], "customer-specific")
        self.assertEqual(account.l10n_es_bank_id, restored_bank)
        self.assertEqual(account.bank_name, "Manual account name")
        self.assertEqual(account.bank_bic, "MANUALBIC")
        self.assertEqual(account.street, "Manual account street")
        self.assertEqual(
            self.env.ref("l10n_es_partner.migration_restored_bank"), restored_bank
        )
        cr.execute("SELECT to_regclass('l10n_es_partner_pre20_res_bank')")
        self.assertFalse(cr.fetchone()[0])

    def test_03_upgrade_without_pre_snapshot_fails_closed(self):
        migration = self._load_migration_script("post-migration.py")
        with self.assertRaisesRegex(RuntimeError, "pre-upgrade"):
            migration.migrate(self.env.cr, "19.0.1.0.3")
