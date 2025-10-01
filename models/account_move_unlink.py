from odoo import models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"
    _description = "Bloqueo de la eliminación de facturas"

    def unlink(self):
        for factura in self:
            if factura.state == "cancel":
                raise ValidationError("No se pueden eliminar los registros.")
        return super(AccountMove, self).unlink()
