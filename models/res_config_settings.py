from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    entorno_pruebas = fields.Boolean(
        default=False,
        string="Usar entorno de pruebas",
        config_parameter="fel.entorno_pruebas",
        company_dependent=True,
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        company = self.env.company
        pruebas = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("fel.entorno_pruebas_%d" % company.id, default=False)
        )
        res.update(entorno_pruebas=pruebas)
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        company = self.env.company
        self.env["ir.config_parameter"].sudo().set_param(
            "fel.entorno_pruebas_%d" % company.id, self.entorno_pruebas
        )
