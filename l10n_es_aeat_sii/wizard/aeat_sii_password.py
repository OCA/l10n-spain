# -*- coding: utf-8 -*-
# (c) 2017 Diagram Software S.L.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from openerp.osv import osv, fields
from openerp.tools.config import config
from openerp.tools.translate import _
from openerp import exceptions
from openerp import release
import contextlib
import OpenSSL.crypto
import os
import tempfile
import base64
import logging

_logger = logging.getLogger(__name__)

if tuple(map(int, OpenSSL.__version__.split('.'))) < (0, 15):
    _logger.warning(
        'OpenSSL version is not supported. Upgrade to 0.15 or greater.')


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


class L10nEsAeatSiiPassword(osv.TransientModel):
    _name = 'l10n.es.aeat.sii.password'

    _columns = {
        'password': fields.char(string="Password", size=64, required=True)
    }

    def get_keys(self, cr, uid, ids, context={}):
        aeat_obj = self.pool['l10n.es.aeat.sii']
        for wizard in self.browse(cr, uid, ids):
            record = self.pool['l10n.es.aeat.sii'].browse(cr, uid, context.get('active_id'), context=context)
            directory = os.path.join(
                os.path.abspath(record.path_folder), 'certificates', cr.dbname, record.folder)
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
                if e.args:
                    args = list(e.args)
                raise exceptions.osv_exception(args[-1])
        return {'type': 'ir.actions.act_window_close'}
