# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

"""Functions for WS-Security (WSSE) signature creation and verification.

Heavily based on test examples in https://github.com/mehcode/python-xmlsec as
well as the xmlsec documentation at https://www.aleksey.com/xmlsec/.

Reading the xmldsig, xmlenc, and ws-security standards documents, though
admittedly painful, will likely assist in understanding the code in this
module.

"""
from lxml import etree
from lxml.etree import QName
import logging
try:
    from zeep import ns
    from zeep.exceptions import SignatureVerificationFailed
    from zeep.utils import detect_soap_env
    from zeep.wsse.utils import ensure_id, get_security_header
    from OpenSSL import crypto
except (ImportError, IOError) as err:
    logging.info(err)
import base64
from datetime import datetime, timedelta

try:
    import xmlsec
except ImportError:
    xmlsec = None

# SOAP envelope
SOAP_NS = 'http://schemas.xmlsoap.org/soap/envelope/'


def _read_file(f_name):
    with open(f_name, "rb") as f:
        return f.read()


def _make_sign_key(key_data, cert_data, password):
    key = xmlsec.Key.from_memory(key_data,
                                 xmlsec.KeyFormat.PKCS12_PEM, password)
    return key


def _make_verify_key(cert_data):
    key = xmlsec.Key.from_memory(cert_data,
                                 xmlsec.KeyFormat.CERT_PEM, None)
    return key


class MemorySignature(object):
    """Sign given SOAP envelope with WSSE sig using given key and cert."""

    def __init__(self, key_data, cert_data, password=None):
        check_xmlsec_import()

        self.key_data = key_data
        self.cert_data = cert_data
        self.password = password

    def apply(self, envelope, headers):
        signed = sign_envelope(envelope, self.key_data, self.cert_data,
                               self.password)
        return signed, headers

    def verify(self, envelope):
        key = _make_verify_key(self.cert_data)
        _verify_envelope_with_key(envelope, key)
        return envelope


class Signature(MemorySignature):
    """Sign given SOAP envelope with WSSE sig using given key file and
    cert file."""

    def __init__(self, key_file, certfile, password=None):
        super(Signature, self).__init__(_read_file(key_file),
                                        _read_file(certfile),
                                        password)


def check_xmlsec_import():
    if xmlsec is None:
        raise ImportError(
            "The xmlsec module is required for wsse.Signature()\n" +
            "You can install xmlsec with: pip install xmlsec\n" +
            "or install zeep via: pip install zeep[xmlsec]\n"
        )


def sign_envelope(envelope, keyfile, certfile, password=None):
    key = _make_sign_key(keyfile, certfile, password)
    reference_id = 'Reference'
    security = get_security_header(envelope)
    security.set(QName(ns.SOAP_ENV_11, 'mustUnderstand'), '1')
    x509type = 'http://docs.oasis-open.org/wss/2004/01/' \
               'oasis-200401-wss-x509-token-profile-1.0#X509v3'
    encoding_type = "http://docs.oasis-open.org/wss/2004/01/" \
                    "oasis-200401-wss-soap-message-security-1.0#Base64Binary"
    binary_token = etree.SubElement(
        security,
        QName(ns.WSSE, 'BinarySecurityToken'),
        attrib={
            QName(ns.WSU, 'Id'): reference_id,
            'ValueType': x509type,
            'EncodingType': encoding_type
        }
    )
    binary_token.text = base64.b64encode(
        crypto.dump_certificate(
            crypto.FILETYPE_ASN1,
            crypto.load_pkcs12(keyfile, password).get_certificate()
        )
    )
    signature = xmlsec.template.create(
        envelope,
        xmlsec.Transform.EXCL_C14N,
        xmlsec.Transform.RSA_SHA1,
        ns='ds'
    )

    # Add a KeyInfo node with X509Data child to the Signature. XMLSec will fill
    # in this template with the actual certificate details when it signs.
    key_info = xmlsec.template.ensure_key_info(signature)
    sec_token_ref = etree.SubElement(
        key_info, QName(ns.WSSE, 'SecurityTokenReference'))
    etree.SubElement(
        sec_token_ref,
        QName(ns.WSSE, 'Reference'),
        attrib={
            'URI': '#' + reference_id,
            'ValueType': x509type
        }
    )
    # Insert the Signature node in the wsse:Security header.

    security.append(signature)

    # Perform the actual signing.
    ctx = xmlsec.SignatureContext()
    ctx.key = key

    timestamp = etree.SubElement(security, QName(ns.WSU, 'Timestamp'))
    now = datetime.now()
    etree.SubElement(timestamp, QName(ns.WSU, 'Created')).text = now.strftime(
        '%Y-%m-%dT%H:%M:%SZ'
    )
    exp = now + timedelta(hours=1)
    etree.SubElement(timestamp, QName(ns.WSU, 'Expires')).text = exp.strftime(
        '%Y-%m-%dT%H:%M:%SZ'
    )

    soap_env = detect_soap_env(envelope)
    _sign_node(ctx, signature, envelope.find(QName(soap_env, 'Body')))
    _sign_node(ctx, signature, security.find(QName(ns.WSU, 'Timestamp')))

    ctx.sign(signature)
    return etree.fromstring(etree.tostring(envelope, method='c14n'))


def verify_envelope(envelope, certfile):
    """Verify WS-Security signature on given SOAP envelope with given cert.

    Expects a document like that found in the sample XML in the ``sign()``
    docstring.

    Raise SignatureVerificationFailed on failure, silent on success.

    """
    key = _make_verify_key(_read_file(certfile))
    return _verify_envelope_with_key(envelope, key)


def _verify_envelope_with_key(envelope, key):
    soap_env = detect_soap_env(envelope)

    header = envelope.find(QName(soap_env, 'Header'))
    if header is None:
        raise SignatureVerificationFailed()

    security = header.find(QName(ns.WSSE, 'Security'))
    signature = security.find(QName(ns.DS, 'Signature'))
    key_text = security.find(QName(ns.WSSE, 'BinarySecurityToken')).text
    key = xmlsec.Key.from_memory(base64.b64decode(key_text),
                                 xmlsec.KeyFormat.CERT_DER, None)
    ctx = xmlsec.SignatureContext()
    # Find each signed element and register its ID with the signing context.
    refs = signature.xpath(
        'ds:SignedInfo/ds:Reference', namespaces={'ds': ns.DS})
    for ref in refs:
        # Get the reference URI and cut off the initial '#'
        referenced_id = ref.get('URI')[1:]
        referenced = envelope.xpath(
            "//*[@wsu:Id='%s']" % referenced_id,
            namespaces={'wsu': ns.WSU},
        )[0]
        ctx.register_id(referenced, 'Id', ns.WSU)

    ctx.key = key
    try:
        ctx.verify(signature)
    except xmlsec.Error:
        # Sadly xmlsec gives us no details about the reason for the failure, so
        # we have nothing to pass on except that verification failed.
        raise SignatureVerificationFailed()


def _sign_node(ctx, signature, target):
    """Add sig for ``target`` in ``signature`` node, using ``ctx`` context.

    Doesn't actually perform the signing; ``ctx.sign(signature)`` should be
    called later to do that.

    Adds a Reference node to the signature with URI attribute pointing to the
    target node, and registers the target node's ID so XMLSec will be able to
    find the target node by ID when it signs.

    """

    # Ensure the target node has a wsu:Id attribute and get its value.
    node_id = ensure_id(target)

    # Unlike HTML, XML doesn't have a single standardized Id. WSSE suggests the
    # use of the wsu:Id attribute for this purpose, but XMLSec doesn't
    # understand that natively. So for XMLSec to be able to find the referenced
    # node by id, we have to tell xmlsec about it using the register_id method.
    ctx.register_id(target, 'Id', ns.WSU)

    # Add reference to signature with URI attribute pointing to that ID.
    ref = xmlsec.template.add_reference(
        signature, xmlsec.Transform.SHA1, uri='#' + node_id)
    # This is an XML normalization transform which will be performed on the
    # target node contents before signing. This ensures that changes to
    # irrelevant whitespace, attribute ordering, etc won't invalidate the
    # signature.
    xmlsec.template.add_transform(ref, xmlsec.Transform.EXCL_C14N)
