from odoo import models, fields, api


class AccountJournal(models.Model):
    _inherit = "account.journal"
    _description = "Enlace para usar los diarios"

    facturacion_activa = fields.Boolean(string="Facturación electrónica", default=False)
    facturas_especiales = fields.Boolean(string="Diario para factura especiales", default=False)

    @api.onchange("facturacion_activa")
    def _onchange_facturacion_activa(self):
        if self.facturacion_activa:
            self.restrict_mode_hash_table = True
        else:
            self.restrict_mode_hash_table = False
