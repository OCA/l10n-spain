# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

"""Functions for WS-Security (WSSE) signature creation and verification.

Heavily based on test examples in https://github.com/mehcode/python-xmlsec as
well as the xmlsec documentation at https://www.aleksey.com/xmlsec/.

Reading the xmldsig, xmlenc, and ws-security standards documents, though
admittedly painful, will likely assist in understanding the code in this
module.

"""
import base64
import logging
from datetime import datetime, timedelta

from lxml import etree
from lxml.etree import QName

try:
    import xmlsig
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization
    from zeep import ns
    from zeep.exceptions import SignatureVerificationFailed
    from zeep.utils import detect_soap_env
    from zeep.wsse.utils import ensure_id, get_security_header
except (ImportError, IOError) as err:
    logging.info(err)

# SOAP envelope
SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"


def _read_file(f_name):
    with open(f_name, "rb") as f:
        return f.read()


class MemorySignature(object):
    """Sign given SOAP envelope with WSSE sig using given key and cert."""

    def __init__(self, public_cert, private_key, cert_data, password=None):
        self.public_cert = public_cert
        self.private_key = private_key
        self.cert_data = cert_data
        self.password = password

    def apply(self, envelope, headers):
        signed = sign_envelope(
            envelope, self.public_cert, self.private_key, self.cert_data, self.password
        )
        return signed, headers

    def verify(self, envelope):
        verify_envelope(envelope, self.cert_data)
        return envelope


class Signature(MemorySignature):
    """Sign given SOAP envelope with WSSE sig using given key file and
    cert file."""

    def __init__(self, key_file, certfile, password=None):
        super(Signature, self).__init__(
            _read_file(key_file), _read_file(certfile), password
        )


def sign_envelope(envelope, public_cert, private_key, certfile, password):
    reference_id = "Reference"
    security = get_security_header(envelope)
    security.set(QName(ns.SOAP_ENV_11, "mustUnderstand"), "1")
    x509type = (
        "http://docs.oasis-open.org/wss/2004/01/"
        "oasis-200401-wss-x509-token-profile-1.0#X509v3"
    )
    encoding_type = (
        "http://docs.oasis-open.org/wss/2004/01/"
        "oasis-200401-wss-soap-message-security-1.0#Base64Binary"
    )
    binary_token = etree.SubElement(
        security,
        QName(ns.WSSE, "BinarySecurityToken"),
        attrib={
            QName(ns.WSU, "Id"): reference_id,
            "ValueType": x509type,
            "EncodingType": encoding_type,
        },
    )
    binary_token.text = base64.b64encode(
        public_cert.public_bytes(encoding=serialization.Encoding.DER)
    )
    signature = xmlsig.template.create(
        c14n_method=xmlsig.constants.TransformExclC14N,
        sign_method=xmlsig.constants.TransformRsaSha1,
        ns="ds",
    )
    envelope.append(signature)

    # Add a KeyInfo node with X509Data child to the Signature. XMLSec will fill
    # in this template with the actual certificate details when it signs.
    key_info = xmlsig.template.ensure_key_info(signature)
    sec_token_ref = etree.SubElement(key_info, QName(ns.WSSE, "SecurityTokenReference"))
    etree.SubElement(
        sec_token_ref,
        QName(ns.WSSE, "Reference"),
        attrib={"URI": "#" + reference_id, "ValueType": x509type},
    )
    # Insert the Signature node in the wsse:Security header.

    security.append(signature)

    # Perform the actual signing.
    ctx = xmlsig.SignatureContext()
    ctx.x509 = public_cert
    ctx.public_key = public_cert.public_key()
    ctx.private_key = private_key

    timestamp = etree.SubElement(security, QName(ns.WSU, "Timestamp"))
    now = datetime.now()
    etree.SubElement(timestamp, QName(ns.WSU, "Created")).text = now.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    exp = now + timedelta(hours=1)
    etree.SubElement(timestamp, QName(ns.WSU, "Expires")).text = exp.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

    soap_env = detect_soap_env(envelope)
    _sign_node(ctx, signature, envelope.find(QName(soap_env, "Body")))
    _sign_node(ctx, signature, security.find(QName(ns.WSU, "Timestamp")))

    ctx.sign(signature)
    return etree.fromstring(etree.tostring(envelope, method="c14n"))


def verify_envelope(envelope, cert):
    """Verify WS-Security signature on given SOAP envelope with given cert.

    Expects a document like that found in the sample XML in the ``sign()``
    docstring.

    Raise SignatureVerificationFailed on failure, silent on success.

    """
    soap_env = detect_soap_env(envelope)

    header = envelope.find(QName(soap_env, "Header"))
    if header is None:
        raise SignatureVerificationFailed()

    security = header.find(QName(ns.WSSE, "Security"))
    signature = security.find(QName(ns.DS, "Signature"))
    key_text = security.find(QName(ns.WSSE, "BinarySecurityToken")).text
    key = x509.load_der_x509_certificate(
        base64.b64decode(key_text), backend=default_backend()
    )
    ctx = xmlsig.SignatureContext()
    ctx.public_key = key.public_key()
    try:
        ctx.verify(signature)
    except Exception:
        # Sadly xmlsec gives us no details about the reason for the failure, so
        # we have nothing to pass on except that verification failed.
        raise SignatureVerificationFailed() from None


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
    # ctx.register_id(target, "Id", ns.WSU)

    # Add reference to signature with URI attribute pointing to that ID.
    ref = xmlsig.template.add_reference(
        signature, xmlsig.constants.TransformSha1, uri="#" + node_id
    )
    # This is an XML normalization transform which will be performed on the
    # target node contents before signing. This ensures that changes to
    # irrelevant whitespace, attribute ordering, etc won't invalidate the
    # signature.
    xmlsig.template.add_transform(ref, xmlsig.constants.TransformExclC14N)
