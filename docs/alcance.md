# Alcance del MVP

## Objetivo

Dar a una pequeña empresa una fuente única y auditable para responder tres preguntas: qué productos tiene, dónde están y qué movimientos explican el saldo.

## Usuarios y permisos

| Capacidad | Administrador | Operador |
|---|:--:|:--:|
| Consultar catálogo, saldo e historial | Sí | Sí |
| Registrar entradas, salidas y ajustes | Sí | Sí |
| Administrar productos, categorías y proveedores | Sí | No |
| Administrar ubicaciones y usuarios | Sí | No |
| Archivar productos | Sí | No |
| Consultar resumen de reposición | Sí | Sí |

Toda autorización se valida en el servidor. Ocultar una acción en la interfaz no sustituye el control de permisos.

## Historias y criterios de aceptación

### Catálogo

- Como administrador, creo y edito productos con SKU, nombre, categoría, unidad y umbral mínimo.
- El sistema rechaza un SKU duplicado y cantidades o umbrales negativos.
- La unidad se mantiene fija después del primer movimiento para no reinterpretar las cantidades históricas.
- Un producto usado en movimientos se puede archivar, pero no eliminar.

### Proveedores

Estado actual: el registro y la desactivación están disponibles en el admin; cada producto admite un proveedor principal. La asociación múltiple y el código de proveedor descritos a continuación quedan pendientes de implementación.

- Como administrador, registro proveedores y los relaciono con productos.
- Puedo marcar un proveedor preferido y guardar un código de producto del proveedor si existe.
- Un proveedor utilizado se desactiva en vez de borrarse.

### Existencias

- Como operador, registro una entrada, salida o ajuste para una ubicación. En ajustes, ingreso el delta firmado del conteo físico.
- Antes de confirmar una salida, el sistema comprueba que exista saldo suficiente.
- Al confirmar, el movimiento y el saldo se actualizan juntos; ante error, no se guarda ninguno.
- El saldo mostrado puede explicarse sumando el saldo inicial y los movimientos confirmados.

### Reposición

- Puedo filtrar productos cuyo saldo total sea menor o igual a su umbral.
- La alerta muestra producto, saldo, mínimo y ubicaciones involucradas.
- El umbral cero desactiva la alerta automática para ese producto.

### Auditoría

- Cada movimiento conserva autor, fecha, tipo, cantidad, ubicación y motivo.
- Un movimiento confirmado no se edita ni elimina desde la interfaz ni desde la API.
- La pantalla de historial es de solo lectura para movimientos confirmados; las correcciones enlazadas quedan para una siguiente iteración.

## Límites de dominio del MVP

- Cantidades expresadas en unidades enteras para simplificar el control inicial. Si se requiere peso o volumen fraccionario, se definirá precisión y redondeo antes de incorporarlo.
- Una organización por instalación. El diseño dejará clara la frontera para una futura separación multiempresa, pero no se implementará aislamiento multi-tenant en el MVP.
- No habrá conversión automática entre unidades.
- No se generarán compras automáticamente: el sistema detecta necesidad de reposición y deja la decisión al usuario.

## Fuera de alcance

Órdenes de compra y recepción parcial, ventas, facturación, lotes y vencimientos, códigos de barra, reservas de stock, integración con ERP, notificaciones por correo y aplicación móvil nativa.

## Entrega verificable

El MVP se considerará listo cuando un operador pueda crear un movimiento, el sistema preserve la integridad bajo intentos de salida inválidos y concurrentes, y otra persona pueda reconstruir el saldo desde el historial. La interfaz deberá cubrir catálogo, detalle de producto, movimiento e informe de reposición.
