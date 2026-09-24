# Estructura inicial

```text
stockflow/
├── config/                  # settings, urls y WSGI
├── apps/
│   └── inventario/          # catálogo, ubicaciones, saldos, movimientos y API
│       ├── management/      # comandos de carga de datos demo
│       ├── migrations/      # esquema de base de datos versionado
│       ├── models.py        # entidades y restricciones
│       ├── services.py      # operaciones de stock transaccionales
│       ├── selectors.py     # (futuro) consultas de lectura reutilizables
│       ├── views.py         # vistas HTML
│       ├── forms.py         # formularios web y validación
│       ├── api.py           # endpoints REST
│       ├── serializers.py   # contratos JSON
│       └── admin.py         # administración con movimientos de solo lectura
├── templates/               # layout, pantallas y acceso
├── static/
│   └── css/                 # estilos compilados/listos para servir
├── docs/                    # alcance, arquitectura, flujos y decisiones
├── .env.example             # nombres de variables, sin secretos
├── manage.py
├── requirements.txt         # dependencias Python
└── README.md
```

## Organización interna de una app

```text
apps/inventario/
├── models.py                # tablas y restricciones locales
├── services.py              # operaciones de dominio transaccionales
├── selectors.py             # consultas de lectura reutilizables
├── api/                     # serializers, vistas y rutas REST
├── views.py                 # vistas HTML
├── forms.py                 # validación de formularios HTML
├── admin.py                 # administración con acciones seguras
├── urls.py
└── tests/                   # pruebas del dominio de inventario
```

La primera versión agrupa el dominio en `apps.inventario` para mantener el arranque pequeño y revisable. Si el dominio crece, catálogo, proveedores y reportes se pueden extraer a apps propias cuando tengan flujos y reglas independientes. La estructura representa lo que existe hoy y marca las futuras separaciones sin fingir que ya están implementadas.
