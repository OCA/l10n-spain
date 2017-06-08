# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Alejandro Sanchez (http://www.asr-oss.com)
#                       Alejandro Sanchez <alejandro@asr-oss.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from . import country
from . import partner
from . import res_company
from . import payment_mode
from . import wizard


def pre_init_hook(cr):
    cr.execute("update ir_model_data set noupdate=false where "
               "module = 'base' and model = 'res.country'")


def post_init_hook(cr, registry):
    cr.execute("update ir_model_data set noupdate=true where "
               "module = 'base' and model = 'res.country'")
