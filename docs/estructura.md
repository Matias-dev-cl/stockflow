# Estructura del repositorio

```text
stockflow/
├── .github/workflows/checks.yml  # controles y suite con PostgreSQL
├── config/                      # configuración, URLs y WSGI
├── apps/inventario/
│   ├── models.py                # entidades y restricciones de base de datos
│   ├── services.py              # registro transaccional de movimientos
│   ├── forms.py                 # formularios completos y rápidos
│   ├── views.py                 # páginas, permisos y paginación
│   ├── api.py                   # endpoints REST
│   ├── serializers.py           # contrato JSON y validación
│   ├── pagination.py            # límites de tamaño de página de API
│   ├── urls.py
│   ├── admin.py                 # administración; stock de solo lectura
│   ├── migrations/              # esquema versionado
│   ├── management/commands/     # cargar_demo
│   └── tests/
│       ├── test_stock.py        # integridad, rollback y concurrencia PostgreSQL
│       ├── test_web_api.py      # permisos, flujos, API y demo
│       └── test_settings.py     # carga de .env y conexión de base de datos
├── templates/
│   ├── base.html
│   ├── registration/
│   ├── inventario/
│   └── partials/pagination.html
├── static/                      # CSS y favicon
├── docs/                        # alcance, arquitectura, flujos y revisión
├── .env.example
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```

La aplicación de dominio se mantiene junta mientras catálogo, proveedores e inventario comparten un flujo pequeño. Si aparecen reglas independientes, se evaluará extraer aplicaciones. Las carpetas vacías de la definición inicial no representan módulos implementados y no se versionan.

`.venv`, `.env`, la base local y los archivos estáticos recopilados no se suben a Git.
