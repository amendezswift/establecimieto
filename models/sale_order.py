from odoo import models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def create_invoices(self):
        res = super(SaleAdvancePaymentInv, self).create_invoices()

        for sale_order in self.env["sale.order"].browse(self._context.get("active_ids", [])):
            for invoice in sale_order.invoice_ids:
                if invoice.move_type == "out_invoice":
                    invoice.update(
                        {
                            "nombre_consignatario": sale_order.partner_id.nombre_consignatario,
                            "direccion_consignatario": sale_order.partner_id.direccion_consignatario,
                            "codigo_consignatario": sale_order.partner_id.codigo_consignatario,
                            "nombre_comprador": sale_order.partner_id.nombre_comprador,
                            "direccion_comprador": sale_order.partner_id.direccion_comprador,
                            "codigo_comprador": sale_order.partner_id.codigo_comprador,
                        }
                    )

        return res
