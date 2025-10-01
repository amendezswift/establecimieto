from odoo import models, fields


class AccountTax(models.Model):
    _inherit = "account.tax"

    nombre_corto = fields.Char(string="Nombre corto")
    codigo_gravable = fields.Integer(string="Codigo gravable")
    unidad_medida = fields.Float(string="Unidad de Medida")
