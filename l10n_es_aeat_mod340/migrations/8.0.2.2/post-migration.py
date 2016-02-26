# -*- coding: utf-8 -*-
##############################################################################
#
#    Otherway Creatives S.L.
#    Copyright (C) 2014-TODAY Otherway Creatives(<http://www.otherway.es>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from openerp import tools
from base64 import b64decode, b64encode
import hashlib, re, os, logging
from datetime import datetime
from openerp.tools.translate import _
import pytz

__name__ = u"Completamos el campo 'supplier_invoice_number' en las facturas"

_logger = logging.getLogger(__name__)

def update_supplier_invoice_number(cr, version):
    
    """
    Completamos el campo 'supplier_invoice_number' en las facturas de 
    proveedor que no lo tienen completado, con el valor del campo 'reference'
    si está establecido o con el propio 'internal_number'
    """
    # Primero facturas emitidas
    cr.execute("""select id, reference, invoice_number  
        from account_invoice 
        where supplier_invoice_number is null and type like 'in_invoice'  
        ;""")
    invoices = cr.fetchall()
    for invoice in invoices:
        invoice_id = invoice[0]
        reference = invoice[1]
        invoice_number = invoice[2]
        
        if reference and reference != '': 
            cr.execute("""UPDATE account_invoice SET 
            supplier_invoice_number = %s WHERE id = %s;""", 
            (reference,invoice_id,))

        elif invoice_number and invoice_number != '': 
            cr.execute("""UPDATE account_invoice SET 
            supplier_invoice_number = %s WHERE id = %s;""", 
            (invoice_number,invoice_id,))

    
def migrate(cr, version):
    if not version:
        return
    update_supplier_invoice_number(cr, version)






