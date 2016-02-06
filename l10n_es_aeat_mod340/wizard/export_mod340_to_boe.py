# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2011-2013 Acysos S.L. (http://acysos.com)
#                       Ignacio Ibeas <ignacio@acysos.com>
#    Copyright (c) 2011 NaN Projectes de Programari Lliure, S.L.
#                       http://www.NaN-tic.com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api, _


class L10nEsAeatMod340ExportToBoe(models.TransientModel):
    _inherit = "l10n.es.aeat.report.export_to_boe"
    _name = "l10n.es.aeat.mod340.export_to_boe"

    @api.multi
    def _get_formatted_declaration_record(self, report):
        """
        Returns a type 1, declaration/company, formated record.

        Format of the record:
            Tipo registro 1 – Registro de declarante:
            Posiciones 	Descripción
            1           Tipo de Registro
            2-4 	Modelo Declaración
            5-8 	Ejercicio
            9-17 	NIF del declarante
            18-57 	Apellidos y nombre o razón social del declarante
            58          Tipo de soporte
            59-67 	Teléfono contacto
            68-107      Apellidos y nombre contacto
            108-120 	Número identificativo de la declaración
            121-122 	Declaración complementaria o substitutiva
            123-135 	Número identificativo de la declaración anterior
            136-137     Periodo
            138-146 	Número total de registros
            147-164 	Importe total de la base imponible
            165-182 	Importe Total de la cuota del impuesto
            183-200 	Importe total de las facturas
            201-390 	Blancos
            391-399 	NIF del representante legal
            400-415 	Sello electrónico
            416-500 	Blancos
        """
        text = super(L10nEsAeatMod340ExportToBoe,
                     self)._get_formatted_declaration_record(report)
        # Periodo
        text += self._formatString(report.period_type, 2)
        # Número total de registros
        text += self._formatNumber(report.number_records, 9)
        # Importe total de la base imponible
        text += self._formatNumber(
            report.total_taxable + report.total_taxable_rec, 15, 2, True)
        # Importe Total de la cuota del impuesto
        text += self._formatNumber(
            report.total_sharetax + report.total_sharetax_rec, 15, 2, True)
        # Importe total de las facturas
        text += self._formatNumber(
            report.total + report.total_rec, 15, 2, True)
        # Blancos
        text += 190 * ' '
        # NIF del representante legal
        text += self._formatString(report.representative_vat, 9)
        # Sello electrónico
        text += self._formatString(report.ean13, 17)
        # Blancos
        text += 84 * ' '
        text += '\r\n'
        assert len(text) == 502, \
            _("The type 1 record must be 500 characters long")
        return text

    @api.multi
    def _get_formatted_invoice_issued(self, report, invoice_issued):
        """
        Returns a type 2, invoice issued, formated record

        Format of the record:
            Tipo de Registro 2 – Registro de facturas emitidas
            Posiciones  Descripción
            1           Tipo de Registro
            2-4         Modelo Declaración
            5-8         Ejercicio
            9-17        NIF del declarante
            18-26       NIF del declarado
            27-35       NIF del representante legal
            36-75       Apellidos y nombre, razón social o
                        denominación del declarado
            76-77       Código país
            78          Clave de identificación en el país de residencia
            79-95       Número de identificación fiscal en el país de
                        residencia. TODO de momento blancos.
            96-98       Blancos
            99          Clave tipo de libro. Constante 'E'.
            100         Clave de operación. Constante ' ' para un solo tipo de
                        IVA. Constante 'C' para varios tipos de IVA. TODO Resto
                        de operaciones. Varios tipos impositivos.
            101-108     Fecha de expedición
            109-116     Fecha de operación. Se consigna la misma que
                        expedición. TODO. Fecha del uso del bien.
            117-121     Tipo impositivo
            122-135     Base imponible
            136-149     Cuota del impuesto
            150-163     Importe total de la factura
            164-177     Base imponible a coste. TODO de momento 0.
            178-217     Identificación de la factura
            218-235     Número de registro TODO No se exactamente que es
            236-243     Número de facturas. Siempre 1. TODO Resumenes de
                        facturas o tickets. Clave A o B.
            244-245     Número de registro. Siempre 1. TODO Facturas con varios
                        asientos. Clave C.
            246-325     Intervalo de acumulación. Vacio. TODO Intervalo de
                        resumenes de facturas o tickets.
            326-365     Identificación de la factura rectificativa. TODO.
            366-370     Tipo recargo de equivalencia. TODO.
            371-384     Cuota recargo de equivalencia. TODO.
            385         Situación del Inmueble #TODO
            386-410     Referencia Catastral #TODO
            411-425     Importe Percibido en Metálico #TODO
            426-429     Ejercicio (cifras del ejercicio en el que se hubieran
                        declarado las operaciones que dan origen al cobro)
                        #TODO
            430-444     Importe percibido por transmisiones de Inmuebles
                        sujetas a IVA. #TODO
            445-500     BLANCOS
        """
        text = ''
        for tax_line in invoice_issued.tax_line_ids:
            # Tipo de Registro
            text += '2'
            # Modelo Declaración
            text += '340'
            # Ejercicio
            text += self._formatString(report.fiscalyear_id.code, 4)
            # NIF del declarante
            text += self._formatString(report.company_vat, 9)
            # NIF del declarado
            if invoice_issued.partner_country_code == 'ES':
                text += self._formatString(invoice_issued.partner_vat, 9)
            else:
                text += self._formatString(' ', 9)
            # NIF del representante legal
            text += self._formatString(invoice_issued.representative_vat, 9)
            # Apellidos y nombre, razón social o denominación del declarado
            text += self._formatString(invoice_issued.partner_id.name, 40)
            # Código país
            text += self._formatString(invoice_issued.partner_country_code, 2)
            # Clave de identificación en el país de residencia
            text += self._formatNumber(invoice_issued.partner_id.vat_type, 1)
            # Número de identificación fiscal en el país de residencia.
            if invoice_issued.partner_country_code != 'ES':
                text += self._formatString(
                    invoice_issued.partner_country_code, 2)
                text += self._formatString(invoice_issued.partner_vat, 15)
            else:
                text += 17 * ' '
            # Blancos
            text += 3 * ' '
            # Clave tipo de libro. Constante 'E'.
            text += 'E'
            # Clave de operación
            if invoice_issued.invoice_id.origin_invoices_ids:
                text += 'D'
            elif len(invoice_issued.tax_line_ids) > 1:
                text += 'C'
            elif invoice_issued.invoice_id.is_ticket_summary == 1:
                text += 'B'
            else:
                text += ' '
            text += self._formatNumber(
                invoice_issued.invoice_id.date_invoice.split('-')[0], 4)
            text += self._formatNumber(
                invoice_issued.invoice_id.date_invoice.split('-')[1], 2)
            text += self._formatNumber(
                invoice_issued.invoice_id.date_invoice.split('-')[2], 2)
            text += self._formatNumber(
                invoice_issued.invoice_id.date_invoice.split('-')[0], 4)
            text += self._formatNumber(
                invoice_issued.invoice_id.date_invoice.split('-')[1], 2)
            text += self._formatNumber(
                invoice_issued.invoice_id.date_invoice.split('-')[2], 2)
            # Tipo impositivo
            text += self._formatNumber(tax_line.tax_percentage * 100, 3, 2)
            # Base imponible
            text += self._formatNumber(tax_line.base_amount, 11, 2, True)
            # Cuota del impuesto
            text += self._formatNumber(tax_line.tax_amount, 11, 2, True)
            # Importe total de la factura
            text += self._formatNumber(
                tax_line.tax_amount + tax_line.base_amount, 11, 2, True)
            # Base imponible a coste.
            text += ' ' + self._formatNumber(0, 11, 2)
            # Identificación de la factura
            text += self._formatString(invoice_issued.invoice_id.number, 40)
            # Número de registro
            sequence_obj = self.env['ir.sequence']
            text += self._formatString(sequence_obj.get('mod340'), 18)
            # Número de facturas
            if invoice_issued.invoice_id.is_ticket_summary == 1:
                text += self._formatNumber(
                    invoice_issued.invoice_id.number_tickets, 8)
            else:
                text += self._formatNumber(1, 8)
            # Número de registros (Desglose)
            text += self._formatNumber(len(invoice_issued.tax_line_ids), 2)
            # Intervalo de identificación de la acumulación
            if invoice_issued.invoice_id.is_ticket_summary == 1:
                text += self._formatString(
                    invoice_issued.invoice_id.first_ticket, 40)
                text += self._formatString(
                    invoice_issued.invoice_id.last_ticket, 40)
            else:
                text += 80 * ' '
            # Identificación factura rectificativa
            text += self._formatString(
                ",".join([x.number for x in
                          invoice_issued.invoice_id.origin_invoices_ids]), 40)
            # Tipo Recargo de equivalencia
            text += self._formatNumber(0, 5)
            # Couta del recargo de equivalencia
            text += ' ' + self._formatNumber(0, 11, 2)
            # Situación del Inmueble #TODO
            text += '0'
            # Referencia Catastral #TODO
            text += 25 * ' '
            # Importe Percibido en Metálico #TODO
            text += 15 * '0'
            # Ejercicio ( cifras del ejercicio en el que se hubieran declarado
            # las operaciones que dan origen al cobro ) #TODO
            text += 4 * '0'
            # TODO: Importe percibido por transmisiones de Inmuebles sujetas a
            # IVA.
            text += 15 * '0'
            # Fecha de Cobro #TODO
            text += 8 * '0'
            # Importes cobrado #TODO
            text += 13 * '0'
            # Medio de pago utilizado #TODO
            text += ' '
            # Cuenta Bancaria o medio de cobro utilizado #TODO
            text += 34 * ' '
            text += '\r\n'
        assert len(text) == 502 * len(invoice_issued.tax_line_ids), (
            _("The type 2 issued record must be 500 characters long for each "
              "Vat registry"))
        return text

    @api.multi
    def _get_formatted_invoice_received(self, report,
                                        invoice_received):
        """Returns a type 2, invoice received, formated record

        Format of the record:
            Tipo de Registro 2 – Registro de facturas recibidas
            Posiciones  Descripción
            1           Tipo de Registro
            2-4         Modelo Declaración
            5-8         Ejercicio
            9-17        NIF del declarante
            18-26       NIF del declarado
            27-35       NIF del representante legal
            36-75       Apellidos y nombre, razón social o denominación del
                        declarado
            76-77       Código país
            78          Clave de identificación en el país de residencia
            79-95       Número de identificación fiscal en el país de
                        residencia. TODO de momento blancos.
            96-98       Blancos
            99          Clave tipo de libro. Constante 'R'.
            100         Clave de operación. Constante ' ' para un solo tipo de
                        IVA.
                        Constante 'C' para varios tipos de IVA. TODO Resto de
                        operaciones. Varios tipos impositivos.
            101-108     Fecha de expedición
            109-116     Fecha de operación. Se consigna la misma que
                        expedición. TODO. Fecha del uso del bien.
            117-121     Tipo impositivo
            122-135     Base imponible
            136-149     Cuota del impuesto
            150-163     Importe total de la factura
            164-177     Base imponible a coste. TODO de momento 0.
            178-217     Identificación de la factura
            218-235     Número de registro TODO No se exactamente que es
            236-243     Número de facturas. Siempre 1. TODO Resumenes de
                        facturas o tickets. Clave A o B.
            244-245     Número de registro. Siempre 1. TODO Facturas con
                        varios asientos. Clave C.
            246-335     Intervalo de acumulación. Vacio. TODO Intervalo de
                        resúmenes de facturas o tickets.
            336-349     Cuota deducible. TODO.
            350-500     Blancos
        """
        text = ''
        for tax_line in invoice_received.tax_line_ids:
            # Tipo de Registro
            text += '2'
            # Modelo Declaración
            text += '340'
            # Ejercicio
            text += self._formatString(report.fiscalyear_id.code, 4)
            # NIF del declarante
            text += self._formatString(report.company_vat, 9)
            # NIF del declarado
            if invoice_received.partner_country_code == 'ES':
                text += self._formatString(invoice_received.partner_vat, 9)
            else:
                text += self._formatString(' ', 9)
            # NIF del representante legal
            text += self._formatString(invoice_received.representative_vat, 9)
            # Apellidos y nombre, razón social o denominación del declarado
            text += self._formatString(invoice_received.partner_id.name, 40)
            # Código país
            text += self._formatString(invoice_received.partner_country_code,
                                       2)
            # Clave de identificación en el país de residencia
            text += self._formatNumber(invoice_received.partner_id.vat_type, 1)
            # Número de identificación fiscal en el país de residencia.
            if invoice_received.partner_country_code != 'ES':
                text += self._formatString(
                    invoice_received.partner_country_code, 2)
                text += self._formatString(invoice_received.partner_vat, 15)
            else:
                text += 17 * ' '
            # Blancos
            text += 3 * ' '
            # Clave tipo de libro. Constante 'R'.
            text += 'R'
            # Clave de operación
            if len(invoice_received.tax_line_ids) > 1:
                text += 'C'
            else:
                text += ' '
            # Fecha de expedición
            text += self._formatNumber(
                invoice_received.invoice_id.date_invoice.split('-')[0], 4)
            text += self._formatNumber(
                invoice_received.invoice_id.date_invoice.split('-')[1], 2)
            text += self._formatNumber(
                invoice_received.invoice_id.date_invoice.split('-')[2], 2)
            # Fecha de operación
            text += self._formatNumber(
                invoice_received.invoice_id.date_invoice.split('-')[0], 4)
            text += self._formatNumber(
                invoice_received.invoice_id.date_invoice.split('-')[1], 2)
            text += self._formatNumber(
                invoice_received.invoice_id.date_invoice.split('-')[2], 2)
            # Tipo impositivo
            text += self._formatNumber(tax_line.tax_percentage * 100, 3, 2)
            # Base imponible
            text += self._formatNumber(tax_line.base_amount, 11, 2, True)
            # Cuota del impuesto
            text += self._formatNumber(tax_line.tax_amount, 11, 2, True)
            # Importe total de la factura
            text += self._formatNumber(tax_line.tax_amount +
                                       tax_line.base_amount, 11, 2, True)
            # Base imponible a coste.
            text += ' ' + self._formatNumber(0, 11, 2)
            # Identificación de la factura
            text += self._formatString(invoice_received.invoice_id.supplier_invoice_number,
                                       40)
            # Número de registro
            sequence_obj = self.env['ir.sequence']
            text += self._formatString(sequence_obj.get('mod340'), 18)
            # Número de facturas
            text += self._formatNumber(1, 18)
            # Número de registros (Desglose)
            text += self._formatNumber(len(invoice_received.tax_line_ids), 2)
            # Intervalo de identificación de la acumulación
            text += 80 * ' '
            # Cuota deducible
            text += ' ' + self._formatNumber(0, 11, 2)
            # Fecha de Pago #TODO
            text += 8 * '0'
            # Importes pagados #TODO
            text += 13 * '0'
            # Medio de pago utilizado
            text += ' '
            # Cuenta Bancaria o medio de cobro utilizado #TODO
            text += 34 * ' '
            # Blancos
            text += 95 * ' '
            text += '\r\n'
        assert len(text) == 502 * len(invoice_received.tax_line_ids), (
            _("The type 2 received record must be 500 characters long for "
              "each Vat registry"))
        return text

    @api.multi
    def _get_formatted_other_records(self, report):
        file_contents = ''
        for invoice_issued in report.issued:
            file_contents += self._get_formatted_invoice_issued(report,
                                                                invoice_issued)
        for invoice_received in report.received:
            file_contents += self._get_formatted_invoice_received(
                report, invoice_received)
        return file_contents
