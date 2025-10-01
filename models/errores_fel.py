from odoo import models, fields


class ErroresFel(models.Model):
    _name = "errores.fel"
    _description = "Manejo de errores INFILE"

    mensaje_error = fields.Char(string="Mensaje de error", copy=False, readonly=True)
    fecha_hora_error = fields.Datetime(string="Fecha y hora", copy=False)
    account_move_factuas_ids = fields.Many2one("account.move")
