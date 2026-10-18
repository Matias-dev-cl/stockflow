# StockFlow

Sistema web de inventario y reposición para pequeñas empresas, construido con Python, Django y Django REST Framework.

> **Estado:** MVP funcional en desarrollo local. Incluye catálogo, movimientos, reposición, edición rápida, archivado reversible y API inicial. El despliegue público sigue pendiente.

## Qué problema resuelve

Cuando las existencias se controlan con planillas y mensajes, resulta difícil saber cuánto hay disponible y explicar las diferencias. StockFlow reúne productos, ubicaciones y movimientos: cada entrada, salida o ajuste conserva su motivo y responsable.

## Qué puedes hacer

- Buscar productos por nombre, SKU o categoría; filtrar activos, archivados y productos por reponer.
- Crear y editar productos como administrador. Al crear uno, abrir su detalle para registrar el stock inicial.
- Registrar entradas, salidas y ajustes desde el detalle, con el producto ya seleccionado.
- Editar rápidamente el nombre y el mínimo de reposición.
- Archivar y reactivar productos sin borrar su historial.
- Consultar saldos por ubicación y recorrer todo el historial mediante paginación.
- Revisar reposición: un mínimo de cero desactiva la alerta.
- Consultar la API y registrar movimientos autenticados.

Categorías, proveedores, ubicaciones y cuentas se administran en el panel de Django. La versión actual admite **un proveedor principal por producto**; múltiples proveedores y códigos de proveedor siguen pendientes.

## Reglas que protege

1. El stock cambia mediante movimientos, nunca editando directamente el saldo desde la interfaz o el admin.
2. Salidas y ajustes no pueden dejar saldo negativo.
3. Cada movimiento requiere una cantidad válida, un motivo y un usuario activo.
4. Registrar el movimiento y actualizar el saldo es una sola transacción.
5. En PostgreSQL se bloquea la fila de saldo para serializar operaciones concurrentes sobre producto y ubicación.
6. Los movimientos confirmados son de solo lectura en web, API y admin.
7. Archivar conserva stock e historial y bloquea nuevos movimientos.
8. Solo administración modifica el catálogo; operadores consultan y registran movimientos.
9. La unidad de un producto se conserva después de su primer movimiento para mantener el significado de las cantidades.

Los ajustes usan una diferencia firmada: si el sistema muestra 10 y contaste 8, registra **-2**. Entradas y salidas reciben cantidades positivas.

## Stack y decisiones

| Tecnología | Función |
|---|---|
| Python + Django | Dominio, autenticación, formularios, administración y vistas HTML |
| Django REST Framework | API autenticada, validación, búsqueda y paginación |
| PostgreSQL / psycopg | Base objetivo para producción y bloqueo concurrente |
| SQLite | Revisión local sin instalar servicios adicionales |
| CSS adaptable | Interfaz web y tarjetas de catálogo en pantallas pequeñas |
| GitHub Actions | Workflow preparado para ejecutar controles y pruebas con PostgreSQL |

## Ejecutar en Windows

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

Abre <http://127.0.0.1:8000>. Cuenta local de demostración: usuario **maty**, contraseña **stockflow-demo**. El comando es repetible y no duplica saldos ni movimientos. Solo funciona con `DEBUG=1`.

El archivo `.env` se carga automáticamente y no se versiona. Sin `DATABASE_URL` se usa SQLite; para PostgreSQL, configura una URL como `postgresql://usuario:clave@localhost:5432/stockflow`. Reinicia el servidor tras cambiar la configuración.

## Comprobar el proyecto

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test apps.inventario.tests
```

La suite cubre reglas de stock, rollback, restricciones de base de datos, permisos, API, archivado, paginación, configuración y datos demo. La prueba concurrente se omite en SQLite porque ese motor no ofrece el bloqueo por fila utilizado; se ejecuta al usar PostgreSQL. El workflow está guardado en [checks.yml](.github/workflows/checks.yml), pendiente de ejecutarse en GitHub.

## API inicial

Requiere autenticación de sesión o autenticación básica de DRF. Para producción, todo acceso debe usar HTTPS.

| Método | Ruta | Resultado |
|---|---|---|
| GET | `/api/v1/productos/` | Productos activos; búsqueda con `?search=texto` |
| GET | `/api/v1/movimientos/` | Historial paginado |
| POST | `/api/v1/movimientos/` | Registra entrada, salida o ajuste |

Las listas devuelven `count`, `next`, `previous` y `results`. Tamaño predeterminado: 25; `?page_size=` permite hasta 100.

Ejemplo de movimiento:

```json
{
  "product": 1,
  "location": 1,
  "kind": "OUT",
  "quantity": 2,
  "reason": "Entrega a operaciones"
}
```

El autor se toma de la sesión autenticada. El cliente no puede atribuir el movimiento a otra persona. La respuesta incluye `delta`, el efecto real sobre el stock.

## Documentación

- [Alcance y límites](docs/alcance.md)
- [Arquitectura y datos](docs/arquitectura.md)
- [Flujos de inventario](docs/flujo.md)
- [Decisiones técnicas](docs/decisiones.md)
- [Estructura del repositorio](docs/estructura.md)
- [Revisión y trabajo pendiente](docs/revision.md)

## Próximos pasos

Validar la suite contra PostgreSQL en un entorno disponible, ejecutar CI en GitHub y preparar el despliegue con HTTPS, credenciales propias, estáticos y copias de respaldo. No basta con cambiar `DEBUG` para publicar la aplicación. Órdenes de compra, facturación, ventas, lotes y códigos de barra quedan fuera de esta primera entrega.
