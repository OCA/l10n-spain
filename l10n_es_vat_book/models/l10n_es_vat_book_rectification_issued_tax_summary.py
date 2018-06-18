# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2017 Praxya (http://praxya.com/)
#                       Daniel Rodriguez Lijo <drl.9319@gmail.com>
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
from openerp import models


class L10nEsVatBookRectificationIssuedTaxSummary(models.Model):
    _inherit = 'l10n.es.vat.book.issued.tax.summary'
    _name = 'l10n.es.vat.book.rectification.issued.tax.summary'
