from odoo import models, fields, api
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"
    _description = "Búsqueda de NIT automatica"

    razon_social = fields.Char(string="Razón social", copy=False, readonly=True, store=True)
    extranjero = fields.Boolean(
        string="Extranjero",
        copy=False,
        default=False,
        compute="_compute_extranjero",
    )
    cui = fields.Char(string="DPI / Pasaporte", copy=False, default=False)
    nombre_consignatario = fields.Char(string="Nombre del consignatario", copy=False)
    direccion_consignatario = fields.Char(string="Dirección del consignatario", copy=False)
    codigo_consignatario = fields.Char(string="Código del consignatario", copy=False)
    nombre_comprador = fields.Char(string="Nombre del comprador", copy=False)
    direccion_comprador = fields.Char(string="Dirección del comprador", copy=False)
    codigo_comprador = fields.Char(string="Código del comprador", copy=False)
    vat = fields.Char(store=True)

    @api.constrains("country_id")
    def _check_country_id(self):
        for contacto in self:
            if not contacto.country_id:
                raise UserError("Debe establecer un país para el contacto")

    @api.depends("country_id")
    def _compute_extranjero(self):
        self.ensure_one()
        if self.country_id.code != "GT":
            self.extranjero = True
        else:
            self.extranjero = False

    @api.model
    def change_contact_language(self):
        partner = self.search([("extranjero", "=", False)])
        for contact in partner:
            contact.lang = "es_419"

    @api.onchange("name", "street")
    def _onchange_name_street(self):
        self.nombre_comprador = self.name
        self.direccion_comprador = self.street
