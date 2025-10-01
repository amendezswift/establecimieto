from odoo import models, fields, api
from odoo.exceptions import UserError


class Establecimientos(models.Model):
    _name = "establecimientos"

    name = fields.Char(string="Nombre comercial", copy=False, required=True)
    codigo = fields.Char(string="Código del establecimiento", copy=False, required=True)
    direccion = fields.Char(string="Dirección", copy=False)
    municipio = fields.Char(string="Municipio")
    departamento = fields.Char(string="Departamento")
    empresa_id = fields.Many2one(
        comodel_name="res.company", string="Empresa", ondelete="cascade", required=True
    )

    @api.constrains("name")
    def _check_name(self):
        for registro in self:
            establecimiento = self.env["establecimientos"].search(
                [
                    ("name", "=", registro.name),
                    ("id", "!=", registro.id),
                    ("empresa_id", "=", registro.empresa_id.id),
                ],
                limit=1,
            )

            if establecimiento:
                raise UserError(
                    "No pueden existir más de un establecimiento con el mismo nombre comercial dentro de la misma empresa."
                )

    @api.constrains("codigo")
    def _check_codigo(self):
        for registro in self:
            establecimiento = self.env["establecimientos"].search(
                [
                    ("codigo", "=", registro.codigo),
                    ("id", "!=", registro.id),
                    ("empresa_id", "=", registro.empresa_id.id),
                ],
                limit=1,
            )

            if establecimiento:
                raise UserError(
                    "No pueden existir más de un establecimiento con el mismo código dentro de la misma empresa."
                )
