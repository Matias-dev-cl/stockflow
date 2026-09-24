# StockFlow

Sistema web de inventario y compras para pequeñas empresas. El objetivo es mantener una existencia confiable por producto y ubicación, registrar cada cambio de stock y ayudar a reponer a tiempo.

> **Estado:** primera versión funcional en desarrollo local. Incluye resumen, catálogo, detalle de producto, movimientos, reposición, login y API inicial.

## Problema

En una pyme, el stock suele repartirse entre planillas, mensajes y memoria. Eso vuelve difícil saber qué hay disponible, explicar diferencias o decidir cuándo comprar. StockFlow centraliza el catálogo, los proveedores y los movimientos, con un historial que permite reconstruir el saldo.

## Alcance del MVP

- Catálogo de productos y categorías, con SKU único, unidad de medida y umbral de reposición.
- Proveedores y datos de contacto; asociación de proveedores preferidos a productos.
- Una o más ubicaciones de almacenamiento.
- Ingresos, salidas y ajustes de inventario con motivo, responsable y fecha.
- Historial cronológico por producto y saldo actual por ubicación.
- Alertas de reposición cuando el disponible llega al umbral configurado.
- Búsqueda, filtros y resumen de productos bajo mínimo.
- Roles de administrador y operador.
- API REST inicial para catálogo y registro de movimientos.

Quedan fuera de la primera versión: órdenes de compra completas, ventas, códigos de barra, lotes y vencimientos, múltiples monedas, facturación y sincronización con sistemas externos. Se dejan como posibles extensiones tras validar el flujo base.

## Reglas centrales

1. El saldo no se edita directamente: se deriva de los movimientos confirmados.
2. Ninguna salida o ajuste puede dejar el saldo disponible bajo cero.
3. Los movimientos confirmados son de solo lectura; el flujo de correcciones compensatorias está definido, pero queda pendiente de implementar.
4. La confirmación de una salida y la actualización del saldo ocurren en una transacción, con bloqueo de la fila de saldo para evitar carreras concurrentes.
5. Cada movimiento identifica producto, ubicación, cantidad, tipo, motivo, usuario y fecha de creación. Los ajustes usan deltas firmados; entradas y salidas usan cantidades positivas.
6. El SKU es único. Los nombres pueden repetirse; el SKU es la referencia operativa estable.
7. Los productos con historial no se borran físicamente: se archivan para preservar trazabilidad.
8. Solo administradores pueden administrar usuarios, ubicaciones y catálogo; operadores pueden consultar y registrar movimientos.

## Stack propuesto

| Tecnología | Uso |
|---|---|
| Python + Django | Dominio, interfaz web, autenticación y administración |
| Django REST Framework | API para operaciones y futuras interfaces |
| CSS adaptable | Interfaz web inicial, sin dependencia de un framework JavaScript |
| PostgreSQL / psycopg | Base relacional prevista y soportada por configuración |

## Documentación

- [Alcance del MVP](docs/alcance.md)
- [Arquitectura y modelo de datos](docs/arquitectura.md)
- [Flujos de inventario](docs/flujo.md)
- [Decisiones técnicas](docs/decisiones.md)
- [Estructura inicial](docs/estructura.md)

La primera entrega todavía no configura GitHub Actions ni un despliegue público. La instalación local está preparada para revisión; el pipeline y el deploy se documentarán al decidir el entorno de publicación.

## Desarrollo

Requiere Python 3.12 o superior.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py cargar_demo
python manage.py runserver
```

Abre <http://127.0.0.1:8000>. Usuario demo `maty`, contraseña `stockflow-demo`. Son credenciales exclusivamente locales para datos ficticios. Para publicar el proyecto se deben cambiar la clave secreta, configurar PostgreSQL y establecer `DEBUG=0`.

Las operaciones de entrada, salida y ajuste usan un servicio transaccional común para la interfaz y la API. En los ajustes, la cantidad ingresada es el delta firmado respecto del saldo actual (por ejemplo `-3` para corregir tres unidades menos). SQLite facilita la revisión local; las garantías de bloqueo concurrente están pensadas para PostgreSQL.
