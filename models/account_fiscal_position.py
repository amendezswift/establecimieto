from odoo import models, fields


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    frases_fel_id = fields.One2many("frases.fel", "fiscal_position_id")
