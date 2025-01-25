{
    "name": "Sale Auto Flow",
    "summary": "This module manages the sale order auto flow.",
    "version": "17.0.0.0",
    "category": "Sales",   
    "author": "Sample Author",
  
    "depends": ["sale_management",'stock'],
   
  
    "data": [
        "security/security.xml",
        "views/sale_order_views.xml",
        "views/res_config_settings_views.xml"
        
      
    ],
    "installable": True,
}
