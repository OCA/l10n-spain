from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    partners = env["res.partner"].search([("comercial", "!=", False)])
    for partner in partners:
        partner._compute_complete_name()
