from odoo import models, fields, api

class MrpProduction(models.Model):
    _inherit = "mrp.production"

    all_components_available = fields.Boolean(compute="_compute_all_components_available")

    @api.depends("move_raw_ids")
    def _compute_all_components_available(self):
        for production in self:
            all_available = True
            for move in production.move_raw_ids:
                if move.product_id.qty_available < 1:
                    all_available = False
                    break
            production.all_components_available = all_available
