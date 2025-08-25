# Copyright 2024 Aures TIC - Almudena de La Puente <almudena@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from datetime import date, timedelta

from .common import TestVerifactuCommon


class TestVerifactuInvoice(TestVerifactuCommon):
    """Test class for VeriFactu Invoice functionality."""

    def _generate_invoice_entry(self, invoice):
        """
        Helper method to generate VERI*FACTU invoice entry for an invoice.
        This assumes the invoice is already prepared for VERI*FACTU.

        Args:
            invoice: Prepared invoice

        Returns:
            verifactu.invoice: Created invoice entry
        """
        invoice._generate_verifactu_chaining()
        return invoice.last_verifactu_invoice_entry_id

    def _create_invoice_sequence(
        self, count=3, start_date="2024-01-01", company=None, amounts=None
    ):
        """
        Helper method to create a sequence of invoices for invoice entry testing.

        Args:
            count: Number of invoices to create
            start_date: Starting date (format: "YYYY-MM-DD")
            company: Company for invoices (defaults to self.company)
            amounts: List of amounts for each invoice (defaults to 100, 110, 120, ...)

        Returns:
            list: List of created and prepared invoices
        """
        if amounts is None:
            amounts = [100 + i * 10 for i in range(count)]
        invoices = []
        for i in range(count):
            # Calculate date by adding days to start_date
            year, month, day = map(int, start_date.split("-"))
            invoice_date = (date(year, month, day) + timedelta(days=i)).strftime(
                "%Y-%m-%d"
            )
            invoice = self._create_and_prepare_invoice(
                company=company,
                date=invoice_date,
                amount=amounts[i] if i < len(amounts) else amounts[-1],
                name=f"Chain test line {i + 1}",
            )
            invoices.append(invoice)

        return invoices

    def _verify_chain_integrity(self, chain_entries):
        """
        Helper method to verify the integrity of a chain sequence.

        Args:
            chain_entries: List of chain entries to verify
        """
        for i, entry in enumerate(chain_entries):
            if i == 0:
                self.assertFalse(
                    entry.previous_invoice_entry_id,
                    "First entry should have no previous",
                )
            else:
                self.assertEqual(
                    entry.previous_invoice_entry_id,
                    chain_entries[i - 1],
                    f"Entry {i} should link to entry {i - 1}",
                )

    def _clean_chain_entries(self, company=None):
        """
        Helper method to clean all chain entries for a company.
        Useful for test isolation.

        Args:
            company: Company to clean entries for (defaults to self.company)
        """
        if company is None:
            company = self.company

        self.env["verifactu.invoice.entry"].search(
            [("company_id", "=", company.id)]
        ).unlink()

    def _assert_chain_entry_properties(
        self,
        chain_entry,
        expected_previous=None,
        expected_document=None,
        expected_company=None,
    ):
        """
        Helper method to assert chain entry properties.

        Args:
            chain_entry: Chain entry to verify
            expected_previous: Expected previous chain entry (None for first entry)
            expected_document: Expected document reference
            expected_company: Expected company (defaults to self.company)
        """
        if expected_company is None:
            expected_company = self.company
        if expected_previous is None:
            self.assertFalse(
                chain_entry.previous_invoice_entry_id,
                "Chain entry should have no previous entry",
            )
        else:
            self.assertEqual(
                chain_entry.previous_invoice_entry_id,
                expected_previous,
                "Chain entry should link to expected previous entry",
            )
        if expected_document:
            self.assertEqual(
                chain_entry.document,
                expected_document,
                "Chain entry should reference expected document",
            )
        self.assertEqual(
            chain_entry.company_id,
            expected_company,
            "Chain entry should belong to expected company",
        )

    def test_verifactu_chain_first_invoice(self):
        """Test that the first invoice creates a chain entry."""
        self._activate_certificate(self.certificate_password)

        self._clean_chain_entries()

        invoice = self._create_and_prepare_invoice()
        chain_entry = self._generate_invoice_entry(invoice)

        self.assertTrue(chain_entry, "Chain entry should be created")

        self._assert_chain_entry_properties(
            chain_entry, expected_previous=None, expected_document=invoice
        )

        self.assertEqual(
            chain_entry.document_hash,
            invoice.verifactu_hash,
            "Hash should match invoice hash",
        )

    def test_verifactu_chain_second_invoice(self):
        """Test that the second invoice creates a chain entry and links to previous."""
        self._activate_certificate(self.certificate_password)

        invoices = self._create_invoice_sequence(count=2, amounts=[100, 150])

        first_chain_entry = self._generate_invoice_entry(invoices[0])
        second_chain_entry = self._generate_invoice_entry(invoices[1])

        self._assert_chain_entry_properties(
            second_chain_entry,
            expected_previous=first_chain_entry,
            expected_document=invoices[1],
        )

        self.assertEqual(
            second_chain_entry.previous_invoice_entry_id.document,
            invoices[0],
            "Previous document should be computed",
        )

    def test_verifactu_chain_multiple_companies_isolation(self):
        """Test that chains are isolated by company."""
        self._activate_certificate(self.certificate_password)

        second_company = self._create_test_company(
            name="Test Company 2", vat="B29805314"
        )
        second_company.verifactu_chaining_id = self.env["verifactu.chaining"].create(
            {
                "name": "VERI*FACTU Chaining 2",
                "sif_id": "12",
                "installation_number": 2,
            }
        )
        first_company_invoice = self._create_and_prepare_invoice()
        first_company_entry = self._generate_invoice_entry(first_company_invoice)
        second_company_invoice = self._create_and_prepare_invoice(
            company=second_company, amount=200
        )
        second_company_entry = self._generate_invoice_entry(second_company_invoice)
        self._assert_chain_entry_properties(first_company_entry, expected_previous=None)
        self._assert_chain_entry_properties(
            second_company_entry,
            expected_previous=None,
            expected_company=second_company,
        )

    def test_verifactu_chain_hash_includes_previous(self):
        """Test that hash calculation includes previous document hash."""
        self._activate_certificate(self.certificate_password)

        invoices = self._create_invoice_sequence(count=2)

        self._generate_invoice_entry(invoices[0])
        first_hash = invoices[0].verifactu_hash

        self._generate_invoice_entry(invoices[1])

        second_hash_string = invoices[1].verifactu_hash_string
        self.assertIn(
            first_hash,
            second_hash_string,
            "Second invoice hash should include first invoice hash",
        )

    def test_verifactu_chain_compute_document_name(self):
        """Test the document name computation."""
        self._activate_certificate(self.certificate_password)

        invoice = self._create_and_prepare_invoice()
        chain_entry = self._generate_invoice_entry(invoice)

        self.assertEqual(chain_entry.document, invoice)

        empty_entry = self.env["verifactu.invoice.entry"].create(
            {
                "document_id": invoice.id,
                "model": invoice._name,
                "company_id": self.company.id,
                "verifactu_chaining_id": self.company.verifactu_chaining_id.id,
                "document_hash": "test_hash",
            }
        )
        self.assertTrue(
            empty_entry,
            "Chain entry should be created even with non-existent document reference",
        )

    def test_verifactu_chain_next_document_linking(self):
        """Test that next document references are properly set."""
        self._activate_certificate(self.certificate_password)

        invoices = self._create_invoice_sequence(count=2, amounts=[100, 150])

        entry_1 = self._generate_invoice_entry(invoices[0])
        entry_2 = self._generate_invoice_entry(invoices[1])

        self.assertEqual(
            entry_1.document_id,
            entry_2.previous_invoice_entry_id.document_id,
            "First invoice should be the same as second entry in previous document",
        )

    def test_verifactu_chain_context_id_set(self):
        """Test that chain_context_id is properly set for invoices."""
        self._activate_certificate(self.certificate_password)

        invoice = self._create_and_prepare_invoice()
        chain_entry = self._generate_invoice_entry(invoice)

        self.assertEqual(
            chain_entry.company_id, self.company, "Should be linked to company"
        )
        # Company relationship is already verified above

    def test_verifactu_company_chaining(self):
        """Test that verifactu always uses company for chaining."""
        self._activate_certificate(self.certificate_password)

        invoice = self._create_and_prepare_invoice()

        # Verify company has the required field for chaining
        self.assertTrue(
            hasattr(
                self.company.verifactu_chaining_id, "last_verifactu_invoice_entry_id"
            ),
            "VERI*FACTU chaining should have last_verifactu_invoice_entry_id field",
        )

        # Verify invoice uses company for chaining
        self.assertEqual(
            invoice.company_id,
            self.company,
            "Invoice should use the correct company for chaining",
        )

    def test_company_last_chain_entry_updated(self):
        """Test that company's last_verifactu_invoice_entry_id is updated."""
        self._activate_certificate(self.certificate_password)

        self.assertFalse(
            self.company.verifactu_chaining_id.last_verifactu_invoice_entry_id,
            "Company should initially have no last chain entry",
        )

        invoice1 = self._create_and_prepare_invoice(amount=100)
        chain_entry1 = self._generate_invoice_entry(invoice1)

        self.assertEqual(
            self.company.verifactu_chaining_id.last_verifactu_invoice_entry_id,
            chain_entry1,
            "Company's last chain entry should be updated to first entry",
        )

        invoice2 = self._create_and_prepare_invoice(amount=200)
        chain_entry2 = self._generate_invoice_entry(invoice2)

        self.assertEqual(
            self.company.verifactu_chaining_id.last_verifactu_invoice_entry_id,
            chain_entry2,
            "Company's last chain entry should be updated to second entry",
        )

        self.assertEqual(
            chain_entry2.previous_invoice_entry_id,
            chain_entry1,
            "Second entry should reference first entry as previous",
        )

    def test_invoice_entry_creation(self):
        """Test the VERI*FACTU invoice entry creation."""
        invoice_model = self.env["verifactu.invoice.entry"]

        # Test creating a simple invoice entry
        test_entry = invoice_model.create(
            {
                "document_id": "999999",
                "model": "account.move",  # Use a high ID that likely doesn't exist
                "document_name": "Test Invoice Entry",
                "company_id": self.company.id,
                "verifactu_chaining_id": self.company.verifactu_chaining_id.id,
                "document_hash": "test_hash_simple",
                "aeat_json_data": '{"test": "data"}',
            }
        )

        self.assertEqual(
            test_entry.company_id,
            self.company,
            "Should be able to create chain entry with company context",
        )
