# -*- coding: utf-8 -*-
# Copyright 2017 Joaquin Gutierrez Pedrosa <joaquin@gutierrezweb.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import models, fields


class AccountHierarchyLabel(models.Model):
    _name = 'account.hierarchy.label'
    _description = 'Account Hierarchy Label'

    name = fields.Char(
        string='Name',
        help="Account name")
    code = fields.Char(
        string='Code',
        required=True,
        help="Account code")
    level = fields.Integer(
        string='Level',
        required=True,
        help="Account level")
