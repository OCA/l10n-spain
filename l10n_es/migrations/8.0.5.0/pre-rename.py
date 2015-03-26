# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Serv. Tecnol. Avanz. (<http://www.serviciosbaeza.com>)
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
#                       FactorLibre (<http://factorlibre.com>)
#                       Hugo santos <hugo.santos@factorlibre.com>
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


def rename_fiscal_positions(cr):
    cr.execute("""
        UPDATE account_fiscal_position
        SET name='Régimen Extracomunitario / Canarias, Ceuta y Melilla'
        WHERE name='Régimen Extracomunitario'
        """)


def rename_tax_codes(cr):
    tax_code_mapping = [
        # Régimen general
        {'previous_code': '[01]', 'code': 'RGIDC4'},
        {'previous_code': '[04]', 'code': 'RGIDC10'},
        {'previous_code': '[07]', 'code': 'RGIDC21'},
        # IVA devengado. Cuota
        {'previous_code': '--',
         'previous_name': 'IVA devengado. Base imponible', 'code': 'IDBI'},
        {'previous_code': '[21]', 'code': 'ITDC'},
        {'previous_code': '[03]', 'code': 'RGIDC4'},
        {'previous_code': '[06]', 'code': 'RGIDC10'},
        {'previous_code': '[09]', 'code': 'RGIDC21'},
        # Adquisiciones intracomunitarias
        {'previous_code': '[20]', 'code': 'AIDBYSC'},
        # IVA deducible. Base Imponible
        {'previous_code': '--',
         'previous_name': 'IVA deducible. Base imponible', 'code': 'ITADC'},
        {'previous_code': '--',
         'previous_name': 'Base de compensaciones Régimen Especial A., G. y'
         ' P. 12%', 'code': 'CREAGYP12'},
        # Base operaciones interiores corrientes
        {'previous_code': '[22]', 'code': 'SOICC'},
        {'previous_code': '--',
         'previous_name': 'Base operaciones interiores corrientes (4%)',
         'code': 'SOICC4'},
        {'previous_code': '--',
         'previous_name': 'Base operaciones interiores corrientes (10%)',
         'code': 'SOICC10'},
        {'previous_code': '--',
         'previous_name': 'Base operaciones interiores corrientes (21%)',
         'code': 'SOICC21'},
        # Base operaciones interiores bienes de inversión
        {'previous_code': '[24]', 'code': 'SOIBIC'},
        {'previous_code': '--',
         'previous_name': 'Base operaciones interiores bienes inversión (4%)',
         'code': 'SOIBIC4'},
        {'previous_code': '--',
         'previous_name': 'Base operaciones interiores bienes inversión (10%)',
         'code': 'SOIBIC10'},
        {'previous_code': '--',
         'previous_name': 'Base operaciones interiores bienes inversión (21%)',
         'code': 'SOIBIC21'},
        # Base importaciones de bienes corrientes
        {'previous_code': '[26]', 'code': 'DIBCC'},
        {'previous_code': '--',
         'previous_name': 'Base importaciones bienes y servicios corrientes'
         ' (4%)', 'code': 'DIBYSCC4'},
        {'previous_code': '--',
         'previous_name': 'Base importaciones bienes y servicios corrientes'
         ' (10%)', 'code': 'DIBYSCC10'},
        {'previous_code': '--',
         'previous_name': 'Base importaciones bienes y servicios corrientes'
         ' (21%)', 'code': 'DIBYSCC21'},
        # Base importaciones de bienes de inversión
        {'previous_code': '[28]', 'code': 'DIBIC'},
        {'previous_code': '--',
         'previous_name': 'Base importaciones bienes inversión (4%)',
         'code': 'DIBIC4'},
        {'previous_code': '--',
         'previous_name': 'Base importaciones bienes inversión (10%)',
         'code': 'DIBIC10'},
        {'previous_code': '--',
         'previous_name': 'Base importaciones bienes inversión (21%)',
         'code': 'DIBIC21'},
        # Adquisiciones intracomunitarias de bienes corrientes
        {'previous_code': '[30]', 'code': 'AIBYSCC'},
        {'previous_code': '--',
         'previous_name': 'Base adquisiciones intracomunitarias bienes y'
         ' serv. corr. (4%)', 'code': 'AIBYSCC4'},
        {'previous_code': '--',
         'previous_name': 'Base adquisiciones intracomunitarias bienes y'
         ' serv. corr. (10%)', 'code': 'AIBYSCC10'},
        {'previous_code': '--',
         'previous_name': 'Base adquisiciones intracomunitarias bienes y'
         ' serv. corr. (21%)', 'code': 'AIBYSCC21'},
        # Adquisiciones intracomunitarias de bienes de inversión
        {'previous_code': '[32]', 'code': 'AIBIC'},
        {'previous_code': '--',
         'previous_name': 'Base adquisiciones intracomunitarias bienes'
         ' inversión (4%)', 'code': 'AIBIC4'},
        {'previous_code': '--',
         'previous_name': 'Base adquisiciones intracomunitarias bienes'
         ' inversión (10%)', 'code': 'AIBIC10'},
        {'previous_code': '--',
         'previous_name': 'Base adquisiciones intracomunitarias bienes'
         ' inversión (21%)', 'code': 'AIBIC21'},
        # Base recargo de equivalencia
        {'previous_code': '--',
         'previous_name': 'Recargo equivalencia ded. Base imponible 0.5%',
         'code': 'REDBI05'},
        {'previous_code': '--',
         'previous_name': 'Recargo equivalencia ded. Base imponible 1.4%',
         'code': 'REDBI014'},
        {'previous_code': '--',
         'previous_name': 'Recargo equivalencia ded. Base imponible 5.2%',
         'code': 'REDBI52'},
        # Iva deducible cuotas
        {'previous_code': '[37]', 'code': 'ITDC'},
        {'previous_code': '34', 'code': 'CREAGYPBI12'},
        # Cuotas operaciones interiores corrientes
        {'previous_code': '[23]', 'code': 'OICBI'},
        {'previous_code': '--',
         'previous_name': 'Cuotas soportadas operaciones interiores corrientes'
         ' (4%)', 'code': 'OICBI4'},
        {'previous_code': '--',
         'previous_name': 'Cuotas soportadas operaciones interiores corrientes'
         ' (10%)', 'code': 'OICBI10'},
        {'previous_code': '--',
         'previous_name': 'Cuotas soportadas operaciones interiores corrientes'
         ' (21%)', 'code': 'OICBI21'},
        # Cuotas operaciones interiores con bienes de inversión
        {'previous_code': '[25]', 'code': 'OIBIBI'},
        {'previous_code': '--',
         'previous_name': 'Cuotas soportadas operaciones interiores bienes'
         ' inversión (4%)', 'code': 'OIBIBI4'},
        {'previous_code': '--',
         'previous_name': 'Cuotas soportadas operaciones interiores bienes'
         ' inversión (10%)', 'code': 'OIBIBI10'},
        {'previous_code': '--',
         'previous_name': 'Cuotas soportadas operaciones interiores bienes'
         ' inversión (21%)', 'code': 'OIBIBI21'},
        # Cuotas devengadas en importaciones de bienes y serv. corr.
        {'previous_code': '[27]', 'code': 'IBCBI'},
        {'previous_code': '--',
         'previous_name': 'Cuotas devengadas importaciones bienes y serv.'
         ' corr. (4%)', 'code': 'IBYSCBI4'},
        {'previous_code': '--',
         'previous_name': 'Cuotas devengadas importaciones bienes y serv.'
         ' corr. (10%)', 'code': 'IBYSCBI10'},
        {'previous_code': '--',
         'previous_name': 'Cuotas devengadas importaciones bienes y serv.'
         ' corr. (21%)', 'code': 'IBYSCBI21'},
        # Cuotas devengadas en importaciones de bienes de inversión
        {'previous_code': '[29]', 'code': 'IBIBI'},
        {'previous_code': '--',
         'previous_name': 'Cuotas devengadas importaciones bienes inversión'
         ' (4%)', 'code': 'IBIBI4'},
        {'previous_code': '--',
         'previous_name': 'Cuotas devengadas importaciones bienes inversión'
         ' (10%)', 'code': 'IBIBI10'},
        {'previous_code': '--',
         'previous_name': 'Cuotas devengadas importaciones bienes inversión'
         ' (21%)', 'code': 'IBIBI21'},
        # Adquisiciones intracomunitarias de bienes corrientes
        {'previous_code': '[31]', 'code': 'AIBYSCBI'},
        {'previous_code': '--',
         'previous_name': 'En adquisiciones intracomunitarias bienes y serv.'
         ' corr. (4%)', 'code': 'AIBYSCBI4'},
        {'previous_code': '--',
         'previous_name': 'En adquisiciones intracomunitarias bienes y serv.'
         ' corr. (10%)', 'code': 'AIBYSCBI10'},
        {'previous_code': '--',
         'previous_name': 'En adquisiciones intracomunitarias bienes y serv.'
         ' corr. (21%)', 'code': 'AIBYSCBI21'},
        # Adquisiciones intracomunitarias bienes de inversión
        {'previous_code': '[33]', 'code': 'AIBIBI'},
        {'previous_code': '--',
         'previous_name': 'En adquisiciones intracomunitarias bienes inversión'
         ' (4%)', 'code': 'AIBIBI4'},
        {'previous_code': '--',
         'previous_name': 'En adquisiciones intracomunitarias bienes inversión'
         ' (10%)', 'code': 'AIBIBI10'},
        {'previous_code': '--',
         'previous_name': 'En adquisiciones intracomunitarias bienes inversión'
         ' (21%)', 'code': 'AIBIBI21'},
        # Otros códigos de impuestos
        {'previous_code': '[42]', 'code': 'EIDBYS'},
        {'previous_code': '[43]', 'code': 'EYOA'},
        # Recargo equivalencia Cuota
        {'previous_code': '[12]',
         'previous_name': 'Recargo equivalencia. Cuota 0.5%',
         'code': 'REC05'},
        {'previous_code': '[15]',
         'previous_name': 'Recargo equivalencia. Cuota 1.4%',
         'code': 'REC014'},
        {'previous_code': '[18]',
         'previous_name': 'Recargo equivalencia. Cuota 5.2%',
         'code': 'REC52'},
        # Recargo equivalencia ded. Cuota
        {'previous_code': '[12]',
         'previous_name': 'Recargo equivalencia ded. Cuota 0.5%',
         'code': 'REDC05'},
        {'previous_code': '[15]',
         'previous_name': 'Recargo equivalencia ded. Cuota 1.4%',
         'code': 'REDC014'},
        {'previous_code': '[18]',
         'previous_name': 'Recargo equivalencia ded. Cuota 5.2%',
         'code': 'REDC52'},
        # Recargo equivalencia base imponible
        {'previous_code': '[10]', 'code': 'REBI05'},
        {'previous_code': '[13]', 'code': 'REBI014'},
        {'previous_code': '[16]', 'code': 'REBI52'},
        # IRPF Retenciones a cuenta
        {'previous_code': 'B.IRPF AC', 'code': 'IRACBI'},
        {'previous_code': 'B.IRPF1 AC', 'code': 'IRACBI1'},
        {'previous_code': 'B.IRPF2 AC', 'code': 'IRACBI2'},
        {'previous_code': 'B.IRPF7 AC', 'code': 'IRACBI7'},
        {'previous_code': 'B.IRPF9 AC', 'code': 'IRACBI9'},
        {'previous_code': 'B.IRPF15 AC', 'code': 'IRACBI15'},
        {'previous_code': 'B.IRPF20 AC', 'code': 'IRACBI20'},
        {'previous_code': 'B.IRPF21 AC', 'code': 'IRACBI21'},
        # IRPF total retenciones a cuenta
        {'previous_code': 'IRPF AC', 'code': 'ITRACC'},
        {'previous_code': 'IRPF1 AC', 'code': 'IRACC1'},
        {'previous_code': 'IRPF2 AC', 'code': 'IRACC2'},
        {'previous_code': 'IRPF7 AC', 'code': 'IRACC7'},
        {'previous_code': 'IRPF9 AC', 'code': 'IRACC9'},
        {'previous_code': 'IRPF15 AC', 'code': 'IRACC15'},
        {'previous_code': 'IRPF20 AC', 'code': 'IRACC20'},
        {'previous_code': 'IRPF21 AC', 'code': 'IRACC21'},
        # IRPF retenciones practicadas. base imponible
        {'previous_code': 'B.IRPF', 'code': 'IRPBI'},
        {'previous_code': 'B.IRPF1', 'code': 'IRPBI1'},
        {'previous_code': 'B.IRPF2', 'code': 'IRPBI2'},
        {'previous_code': 'B.IRPF7', 'code': 'IRPBI7'},
        {'previous_code': 'B.IRPF9', 'code': 'IRPBI9'},
        {'previous_code': 'B.IRPF15', 'code': 'IRPBI15'},
        {'previous_code': 'B.IRPF20', 'code': 'IRPBI20'},
        {'previous_code': 'B.IRPF21', 'code': 'IRPBI21'},
        # IRPF retenciones practicadas. total cuota
        {'previous_code': 'IRPF', 'code': 'ITRPC'},
        {'previous_code': 'IRPF1', 'code': 'IRPC1'},
        {'previous_code': 'IRPF2', 'code': 'IRPC2'},
        {'previous_code': 'IRPF7', 'code': 'IRPC7'},
        {'previous_code': 'IRPF9', 'code': 'IRPC9'},
        {'previous_code': 'IRPF15', 'code': 'IRPC15'},
        {'previous_code': 'IRPF20', 'code': 'IRPC20'},
        {'previous_code': 'IRPF21', 'code': 'IRPC21'}
    ]

    for mapping in tax_code_mapping:
        sql = """
        UPDATE account_tax_code
        SET code='%s'
        WHERE code='%s'""" % (mapping['code'], mapping['previous_code'])

        if mapping.get('previous_name'):
            sql = "%s AND name='%s'" % (sql, mapping['previous_name'])
        cr.execute(sql)


def migrate(cr, version):
    if not version:
        return
    rename_fiscal_positions(cr)
    rename_tax_codes(cr)
