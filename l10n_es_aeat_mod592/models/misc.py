# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _

DOCUMENT_TYPES = [
    ("1", _("(1) NIF or Spanish NIE")),
    ("2", _("(2) Intra-Community VAT NIF")),
    ("3", _("(3) Others")),
]
PRODUCT_KEYS = [
    ("A", _("(A) Non-reusable")),
    ("B", _("(B) Semi-finished")),
    ("C", _("(C) Plastic product intended to allow the closure")),
]
FISCAL_ACQUIRERS = [
    ("A", _("(A) Subjection and non-exemption Law 7/2022, of April 8")),
    ("B", _("(B) Non-subjection article 73 c) Law 7/2022, of April 8")),
    ("C", _("(C) Not subject to article 73 d) Law 7/2022, of April 8")),
    ("D", _("(D) Exemption article 75 a) 1º Law 7/2022, of April 8")),
    ("E", _("(E) Exemption article 75 a) 2º Law 7/2022, of April 8")),
    ("F", _("(F) Exemption article 75 a) 3º Law 7/2022, of April 8")),
    ("G", _("(G) Exemption article 75 b) Law 7/2022, of April 8")),
    ("H", _("(H) Exemption article 75 c) Law 7/2022, of April 8")),
    ("I", _("(I) Exemption article 75 d) Law 7/2022, of April 8")),
    ("J", _("(J) Exemption article 75 e) Law 7/2022, of April 8")),
    ("K", _("(K) Exemption article 75 f) Law 7/2022, of April 8")),
    ("L", _("(L) Exemption article 75 g) 1º Law 7/2022, of April 8")),
    ("M", _("(M) Exemption article 75 g) 2º Law 7/2022, of April 8")),
]
FISCAL_MANUFACTURERS = [
    ("A", _("(A) Subjection and non-exemption ")),
    ("B", _("(B) Not subject to article 73 a) Law 7/2022, of April 8")),
    ("C", _("(C) Not subject to article 73 b) Law 7/2022, of April 8")),
    ("D", _("(D) Non-subjection article 73 c) Law 7/2022, of April 8")),
    ("E", _("(E) Not subject to article 73 d) Law 7/2022, of April 8")),
    ("F", _("(F) Exemption article 75 a) 1º Law 7/2022, of April 8")),
    ("G", _("(G) Exemption article 75 a) 2º Law 7/2022, of April 8")),
    ("H", _("(H) Exemption article 75 a) 3º Law 7/2022, of April 8")),
    ("I", _("(I) Exemption article 75 c) Law 7/2022, of April 8")),
    ("J", _("(J) Exemption article 75 g) 1º Law 7/2022, of April 8")),
    ("K", _("(K) Exemption article 75 g) 2º Law 7/2022, of April 8")),
]
