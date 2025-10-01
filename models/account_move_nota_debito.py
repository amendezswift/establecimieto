from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = "account.move"

    nota_debito = fields.Boolean(string="Es nota de débito", default=False, compute="_compute_nota_debito")

    @api.model
    def default_get(self, field_list):
        res = super(AccountMove, self).default_get(field_list)
        if self.env.context.get("default_nota_debito", False):
            res["nota_debito"] = True
        return res

    @api.depends("debit_origin_id")
    def _compute_nota_debito(self):
        for factura in self:
            if factura.debit_origin_id:
                factura.nota_debito = True
            else:
                factura.nota_debito = False
