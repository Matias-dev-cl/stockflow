# StockFlow

[![Pruebas](https://github.com/Matias-dev-cl/stockflow/actions/workflows/checks.yml/badge.svg?branch=main)](https://github.com/Matias-dev-cl/stockflow/actions/workflows/checks.yml)
[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](requirements.txt)
[![Django](https://img.shields.io/badge/Django-backend-092E20?logo=django&logoColor=white)](config/)

Sistema web de inventario y reposición para pequeñas empresas, construido con Python, Django y Django REST Framework.

![Dashboard de StockFlow: vista inicial completa con indicadores de stock, actividad reciente, alertas de reposición y navegación](docs/capturas/dashboard.jpg)

El dashboard es la pantalla de entrada: permite revisar el estado del inventario y decidir qué necesita atención antes de entrar a cada producto.

Proyecto de portafolio de [Matías Muñoz](https://github.com/Matias-dev-cl). Demuestra desarrollo full stack, lógica de negocio, validaciones, transacciones y pruebas automatizadas.

> **Estado:** MVP funcional con demo local y datos ficticios. El código es público; la aplicación todavía no tiene una URL de despliegue público.

## Qué problema resuelve

Cuando las existencias se controlan con planillas y mensajes, resulta difícil saber cuánto hay disponible y explicar las diferencias. StockFlow reúne productos, ubicaciones y movimientos: cada entrada, salida o ajuste conserva su motivo y responsable.

## Vistas complementarias

Capturas completas con datos ficticios. Abre cada sección o haz clic en una imagen para verla en su resolución original.

<details>
<summary>Catálogo de productos</summary>

![Catálogo completo de productos, con filtros, existencias y acciones de edición](docs/capturas/catalogo.jpg)

</details>

<details>
<summary>Detalle y acciones rápidas</summary>

![Detalle completo del producto, con movimientos, edición rápida, ubicaciones e historial](docs/capturas/detalle.jpg)

</details>

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
git clone https://github.com/Matias-dev-cl/stockflow.git
cd stockflow
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

La suite incluye 38 pruebas sobre reglas de stock, rollback, restricciones de base de datos, permisos, API, archivado, paginación, configuración, caché de estilos y datos demo. La prueba concurrente se omite en SQLite porque ese motor no ofrece el bloqueo por fila utilizado; se ejecuta al usar PostgreSQL. El [workflow](.github/workflows/checks.yml) utiliza PostgreSQL 16 y el estado de cada ejecución puede consultarse en [GitHub Actions](https://github.com/Matias-dev-cl/stockflow/actions).

Las 38 pruebas, incluida la de concurrencia, aprobaron en [la primera ejecución con PostgreSQL en GitHub](https://github.com/Matias-dev-cl/stockflow/actions/runs/39164187677).

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

Preparar una demo pública con HTTPS, credenciales propias, estáticos y copias de respaldo. El código y el historial ya son públicos, y CI valida las reglas contra PostgreSQL. Órdenes de compra, facturación, ventas, lotes y códigos de barra quedan fuera de esta primera entrega.
