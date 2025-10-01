from odoo import models, fields, api
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    autorizacion_proveedor = fields.Char(
        string="Número de autorización", copy=False, default=""
    )
    serie_proveedor = fields.Char(string="Número de serie", copy=False)
    dte_proveedor = fields.Char(string="Número de DTE", copy=False)
    emision_proveedor = fields.Date(string="Fecha de emisión", copy=False)

    @api.constrains("info_factura", "move_type", "state")
    def _check_vendor_info(self):
        for factura in self:
            if (
                factura.move_type in ["in_invoice", "in_refund"]
                and factura.dte_proveedor
                and factura.serie_proveedor
            ):
                dominio = [
                    ("id", "!=", factura.id),
                    ("move_type", "in", ["in_invoice", "in_refund"]),
                    ("state", "=", "posted"),
                    ("serie_proveedor", "=", factura.serie_proveedor),
                    ("dte_proveedor", "=", factura.dte_proveedor),
                ]

                duplicado = self.env["account.move"].search(
                    dominio,
                    limit=1,
                )

                if duplicado:
                    raise UserError(
                        f"Número de serie o DTE ya existentes en el documento: '{duplicado.name}'"
                    )

    @api.model
    def create(self, vals):
        if "dte_proveedor" in vals and vals["dte_proveedor"]:
            vals["dte_proveedor"] = vals["dte_proveedor"].strip().upper()
        if "serie_proveedor" in vals and vals["serie_proveedor"]:
            vals["serie_proveedor"] = vals["serie_proveedor"].strip().upper()

        return super(AccountMove, self).create(vals)

    def write(self, vals):
        if "dte_proveedor" in vals and vals["dte_proveedor"]:
            vals["dte_proveedor"] = vals["dte_proveedor"].strip().upper()
        if "serie_proveedor" in vals and vals["serie_proveedor"]:
            vals["serie_proveedor"] = vals["serie_proveedor"].strip().upper()

        return super(AccountMove, self).write(vals)
