from odoo import fields, models


class FrasesFel(models.Model):
    _name = "frases.fel"
    _description = "Frases FEL para las posiciones fiscales"

    fiscal_position_id = fields.Many2one("account.fiscal.position")
    name = fields.Char(string="Nombre")
    tipo_frase = fields.Integer(string="Tipo de frase")
    codigo_escenario = fields.Integer(string="Código de escenario")
    descripcion = fields.Char(string="Descripción")
