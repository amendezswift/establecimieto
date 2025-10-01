from odoo import models, fields


class WizardAnularFactura(models.TransientModel):
    _name = "wizard.anular.factura"
    _description = "Asistente de anulación"

    motivo_anulacion = fields.Char(string="Motivo de anulación", required=True)
    factura_id = fields.Many2one("account.move", string="Factura", required=True)

    def action_anular_factura(self):
        self.ensure_one()
        factura = self.factura_id
        factura.motivo_anulacion = self.motivo_anulacion
        factura.boton_anular()
