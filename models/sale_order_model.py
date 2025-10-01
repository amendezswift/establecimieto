from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_invoice(self):
        vals = super()._prepare_invoice()
        almacen = self.warehouse_id

        if almacen.establecimiento_id:
            vals["establecimiento_id"] = almacen.establecimiento_id.id

        return vals
