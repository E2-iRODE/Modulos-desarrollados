{
    'name': 'Seguimiento de Ventas',
    'version': '1.0',
    'summary': 'Seguimiento de ventas',
    'category': 'ventas',
   
    'depends': [
        'base',
        'sale',
        'stock',
        'sale_stock',
        'repair_custom',
         'mail'
        
        
        
    ],

    'data': [
         'security/security.xml',   
         'security/ir.model.access.csv',
        'views/secuencia.xml',
        'views/kanba_product.xml',
        'views/after_sale_view.xml',
        'views/res_patner_view.xml',
        'views/wizard_search.xml',
        'views/wizard_search_new_order.xml',
        
        
        
        
        
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
