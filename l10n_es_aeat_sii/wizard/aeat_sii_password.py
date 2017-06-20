# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
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


from osv import osv, fields
from tools.translate import _
from openerp.tools import config
import exceptions
import contextlib
import OpenSSL.crypto
import os
import tempfile
import base64
import logging

_logger = logging.getLogger(__name__)

@contextlib.contextmanager
def pfx_to_pem(file, pfx_password, directory=None):
    with tempfile.NamedTemporaryFile(
            prefix='private_', suffix='.pem', delete=False,
            dir=directory) as t_pem:
        f_pem = open(t_pem.name, 'wb')
        p12 = OpenSSL.crypto.load_pkcs12(file, pfx_password)
        f_pem.write(OpenSSL.crypto.dump_privatekey(
            OpenSSL.crypto.FILETYPE_PEM, p12.get_privatekey()))
        f_pem.close()
        yield t_pem.name


@contextlib.contextmanager
def pfx_to_crt(file, pfx_password, directory=None):
    with tempfile.NamedTemporaryFile(
            prefix='public_', suffix='.crt', delete=False,
            dir=directory) as t_crt:
        f_crt = open(t_crt.name, 'wb')
        p12 = OpenSSL.crypto.load_pkcs12(file, pfx_password)
        f_crt.write(OpenSSL.crypto.dump_certificate(
            OpenSSL.crypto.FILETYPE_PEM, p12.get_certificate()))
        f_crt.close()
        yield t_crt.name


class L10nEsAeatSiiPassword(osv.osv_memory):
    _name = 'l10n.es.aeat.sii.password'

    _columns = {
        'password': fields.char('Password', size=64, required=True)
    }

    def get_keys(self, cr, uid, ids, context=None):
        aeat_obj = self.pool['l10n.es.aeat.sii']
        for wizard in self.browse(cr, uid, ids):
            record = self.pool.get('l10n.es.aeat.sii').browse(cr, uid, context.get('active_id'), context=context)
            path = self.pool.get('ir.config_parameter').get_param(cr, uid, 'l10n_es_aeat_sii.path_folder', '/')
            directory = os.path.join(os.path.abspath(path), 'certificates', cr.dbname, record.folder)
            file = base64.decodestring(record.file)
            if tuple(map(int, OpenSSL.__version__.split('.'))) < (0, 15):
                raise exceptions.Warning(
                    _('OpenSSL version is not supported. Upgrade to 0.15 '
                      'or greater.'))
            try:
                if directory and not os.path.exists(directory):
                    os.makedirs(directory)
                with pfx_to_pem(file, wizard.password, directory) as private_key:
                    aeat_obj.write(cr, uid, record.id, {'private_key': private_key})
                with pfx_to_crt(file, wizard.password, directory) as public_key:
                    aeat_obj.write(cr, uid, record.id, {'public_key': public_key})
            except Exception as e:
                raise(e)

        return {'type': 'ir.actions.act_window_close'}