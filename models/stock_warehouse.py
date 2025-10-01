from odoo import models, fields


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    establecimiento_id = fields.Many2one(
        comodel_name="establecimientos", string="Establecimiento para facturación"
    )
