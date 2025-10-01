from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = "account.move"
    _description = "Modulo con lógica de exportación"

    nombre_consignatario = fields.Char(string="Nombre del consignatario", copy=False)
    direccion_consignatario = fields.Char(string="Dirección del consignatario", copy=False)
    codigo_consignatario = fields.Char(string="Código del consignatario", copy=False)
    nombre_comprador = fields.Char(string="Nombre del comprador", copy=False)
    direccion_comprador = fields.Char(string="Dirección del comprador", copy=False)
    codigo_comprador = fields.Char(string="Código del comprador", copy=False)
    referencia = fields.Char(string="Referencia", copy=False, default="EXPORTACION")

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        self.nombre_consignatario = self.partner_id.nombre_consignatario
        self.direccion_consignatario = self.partner_id.direccion_consignatario
        self.codigo_consignatario = self.partner_id.codigo_consignatario
        self.nombre_comprador = self.partner_id.nombre_comprador
        self.direccion_comprador = self.partner_id.direccion_comprador
        self.codigo_comprador = self.partner_id.codigo_comprador
