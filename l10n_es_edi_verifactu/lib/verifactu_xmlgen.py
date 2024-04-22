# -*- coding: utf-8 -*-
# Copyright 2024 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import os
import subprocess

OPERATION_CREATE = "verifactu_create"
OPERATION_CANCEL = "verifactu_cancel"


def get_credentials(odoo_env, company):
    license_dict = company.get_l10n_es_verifactu_license_dict()
    credentials = {
        "software-developer-name": license_dict.get("developer_name"),
        "software-developer-id": license_dict.get("developer_id"),
        "software-id": license_dict.get("software_id"),
        "software-number": license_dict.get("software_number"),
        "software-name": license_dict.get("software_name"),
        "software-version": license_dict.get("software_version"),
        "testing": company.l10n_es_edi_test_env,
    }
    return credentials


def verifactu_xmlgen(operation, data, odoo_env, company):
    credentials = get_credentials(odoo_env, company)
    # sudo() why: ir.config_parameter is only accessible for base.group_system
    cmd_param = (
        odoo_env["ir.config_parameter"]
        .sudo()
        .get_param("l10n_es_edi_verifactu.verifactu_xml_cmd", False)
    )
    addon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
    cmd_verifactu_xmlgen = (
        cmd_param % {"addon_dir": addon_dir} if cmd_param else "verifactu-xmlgen"
    )
    cmd = [
        cmd_verifactu_xmlgen,
        "-o",
        operation,
        "-s",
        credentials["software-developer-name"],
        "-d",
        credentials["software-developer-id"],
        "-i",
        credentials["software-id"],
        "-h",
        credentials["software-number"],
        "-n",
        credentials["software-name"],
        "-v",
        credentials["software-version"],
    ]
    if credentials.get("testing"):
        cmd.append("-e")
    try:
        sub_env = os.environ.copy()
        return subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            input=data.encode("utf-8"),
            env=sub_env,
        )
    except Exception:
        raise RuntimeError("Could not execute command %r" % cmd[0])
