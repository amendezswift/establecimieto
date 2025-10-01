from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = "account.move"

    exento_iva = fields.Boolean(
        string="Exento", default=False, copy=False, compute="_compute_exento_iva"
    )
    frase_base_ids = fields.Many2one(
        comodel_name="frases.fel", string="Seleccione frase base legal"
    )

    @api.depends("invoice_line_ids.tax_ids")
    def _compute_exento_iva(self):
        for factura in self:
            if any(
                "IVA 0%" in impuesto.name
                for linea in factura.invoice_line_ids
                for impuesto in linea.tax_ids
            ):
                self.exento_iva = True
            else:
                self.exento_iva = False
