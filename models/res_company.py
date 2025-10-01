from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = "res.company"
    _description = "Ampliación de la información de las empresas."

    codigo_exportador = fields.Char(string="Código de exportador")
    nombre_comercial = fields.Char(string="Nombre comercial")
    nombre_emisor = fields.Char(string="Nombre emisor")
    establecimiento_ids = fields.One2many(
        comodel_name="establecimientos", inverse_name="empresa_id", required=True, copy=False
    )

    @api.onchange("tipo_contribuyente")
    def _onchange_contribuyente(self):
        if self.tipo_contribuyente != "general":
            self.retenedor_iva = False
        if self.tipo_contribuyente != "general":
            self.regimen_isr = "none"
