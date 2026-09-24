# Arquitectura y modelo de datos

## Modelo de dominio

```mermaid
erDiagram
    USUARIO ||--o{ MOVIMIENTO : registra
    CATEGORIA ||--o{ PRODUCTO : clasifica
    PRODUCTO ||--o{ SALDO : mantiene
    UBICACION ||--o{ SALDO : contiene
    PRODUCTO ||--o{ MOVIMIENTO : afecta
    UBICACION ||--o{ MOVIMIENTO : ocurre_en
    PRODUCTO ||--o{ PRODUCTO_PROVEEDOR : compra_a
    PROVEEDOR ||--o{ PRODUCTO_PROVEEDOR : ofrece
    MOVIMIENTO o|--o| MOVIMIENTO : corrige

    PRODUCTO {
        string sku UK
        string nombre
        string unidad
        int minimo_reposicion
        bool activo
    }
    SALDO {
        int cantidad
        datetime actualizado_en
        unique producto_ubicacion
    }
    MOVIMIENTO {
        string tipo "ENTRADA | SALIDA | AJUSTE"
        int cantidad "positiva"
        string motivo
        datetime creado_en
        string estado "CONFIRMADO"
        fk movimiento_corregido
    }
    UBICACION {
        string codigo UK
        string nombre
        bool activa
    }
    PROVEEDOR {
        string nombre
        string email
        bool activo
    }
    PRODUCTO_PROVEEDOR {
        string sku_proveedor
        bool preferido
        unique producto_proveedor
    }
```

## Fuente de verdad del saldo

`Movimiento` es el libro de eventos: cada fila confirmada representa un cambio y no se reescribe. `Saldo` es una proyección materializada por par producto–ubicación que permite consultas rápidas. Ambos se modifican en una sola transacción. El saldo debe poder reconstruirse a partir de movimientos; una tarea de auditoría o comando de gestión podrá recalcularlo y detectar diferencias.

La dirección del efecto la determina `tipo`: entrada suma, salida resta y ajuste aplica una diferencia explícita respecto del saldo contado. En el ajuste se almacena la cantidad del delta con signo, mientras que entradas y salidas requieren cantidad positiva. Esta convención se valida en el modelo de dominio/servicio, no solo en formularios.

## Integridad y concurrencia

- Restricción única para SKU y para el par producto–ubicación de `Saldo`.
- Cantidad de saldo nunca negativa; cantidades y mínimos se validan según tipo.
- Crear movimiento y cambiar saldo dentro de `transaction.atomic()`.
- Bloquear la fila `Saldo` correspondiente con `select_for_update()` antes de validar una salida. Crear saldo inicial de forma segura si aún no existe.
- El cliente no puede enviar directamente un saldo final; la API recibe tipo, cantidad, ubicación y motivo.
- Usar borrado protegido para categorías/proveedores referenciados y archivado lógico para entidades con historial.
- Indexar SKU, estado activo, fecha de movimiento y producto/ubicación para las consultas frecuentes.

## Límites de aplicaciones

- `catalogo`: productos y categorías.
- `proveedores`: proveedores y relación con productos.
- `inventario`: ubicaciones, saldos, movimientos y servicio transaccional.
- `usuarios`: usuario y roles.
- `reportes`: consultas de bajo stock y agregados de lectura; no escribe movimientos.

La operación de stock se concentra en un servicio de dominio de `inventario`; las vistas web, el admin y la API llaman al mismo servicio. Así las reglas se mantienen iguales sin importar el punto de entrada.

## API inicial

Prefijo `/api/v1/` implementado inicialmente:

- `GET /api/v1/productos/`
- `GET /api/v1/movimientos/`
- `POST /api/v1/movimientos/` (entrada, salida o ajuste)

Las vistas HTML implementan catálogo, detalle de producto, movimientos y reposición. Endpoints de detalle, filtros avanzados, paginación y documentación OpenAPI quedan como trabajo posterior. Las escrituras devuelven el movimiento confirmado y la API no expone operaciones para borrar o editar movimientos confirmados.
