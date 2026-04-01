{
    'name': 'Colores Etapas',
    'version': '1.0',
    'summary': '',
   'depends': [
        'project',       
        'industry_fsm',  
    ],
    'data': [
        'views/fsm_stage_colors_views.xml'
        
    ],
    'assets': {
        'web.assets_backend': [
            'colors_service_external/static/src/css/fsm_stage_colors_.css',
        ],},
    'installable': True,
    'auto_install': False,
    'application': False,
}
