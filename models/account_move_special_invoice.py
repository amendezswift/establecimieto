from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = "account.move"
    _description = "Control de facturas especiales"

    factura_especial = fields.Boolean(string="Es factura especial", default=False)

    @api.model
    def default_get(self, fields_list):
        res = super(AccountMove, self).default_get(fields_list)
        if res.get("factura_especial"):
            diario = self.env["account.journal"].search([("name", "=", "FACTURAS ESPECIALES")], limit=1)
            if diario:
                res["journal_id"] = diario.id

        if self.env.context.get("default_factura_especial", False):
            res["factura_especial"] = True
        return res
