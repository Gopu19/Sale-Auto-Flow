from odoo import models,fields,api

class ResConfigSettings(models.TransientModel):
    _inherit="res.config.settings"
    
    
   
    sale_order_limit=fields.Float(string="Sale Order Limit",config_parameter='sale_auto_flow.sale_order_limit')