# Decisiones técnicas

## Un servicio para cambiar stock

`record_movement` concentra validaciones y transacción. Tanto los formularios completos y rápidos como DRF pasan por él. El admin impide modificar saldos o movimientos directamente.

## Historial como explicación; saldo como proyección

La suma de los efectos de movimientos debe explicar el saldo de cada producto y ubicación. Mantener el saldo permite lecturas rápidas sin volver a sumar todo el historial en cada petición.

## PostgreSQL como objetivo

La operación de salida depende del bloqueo de fila para serializar solicitudes concurrentes. SQLite reduce la fricción al revisar la aplicación, pero no ofrece esa garantía. Por eso la prueba de concurrencia se ejecuta solo con un motor compatible y el workflow utiliza PostgreSQL.

## Cantidades enteras y ajustes firmados

El MVP maneja unidades enteras. Los movimientos de entrada/salida requieren un número positivo; el ajuste registra la diferencia, por ejemplo -2. El servicio evita saldos negativos y desbordamientos del rango entero de la base.

## Archivado reversible

El historial no se borra cuando un producto sale del catálogo activo. El producto puede consultarse desde movimientos o desde el filtro Archivados y reactivarse. Archivar impide nuevos movimientos, pero no elimina el saldo anterior.

## Roles simples

Se utiliza el usuario de Django y `is_staff` para distinguir administración en la web. La autorización se valida en el servidor; no depende de ocultar un botón. El admin conserva el sistema de permisos por modelo de Django.

## Una empresa y un proveedor principal por producto

La instalación representa una sola organización. Cada producto admite un proveedor principal opcional. Múltiples proveedores, códigos externos y separación entre empresas necesitan un requisito y una ampliación explícita del modelo.

## Interfaz HTML y CSS

La aplicación actual usa plantillas Django y CSS adaptable. El catálogo cambia a tarjetas en pantallas pequeñas. Tailwind se propuso en el diseño inicial, pero no forma parte de la implementación actual.

## API versionada y paginada

La API usa `/api/v1/`, exige autenticación y limita las listas para que no crezcan sin control. El autor se toma de la sesión y no de un campo enviado por el cliente.

## Pendiente antes de publicar

Despliegue HTTPS, almacenamiento de estáticos, respaldo de base, cuentas y secretos propios, y validación real contra PostgreSQL. Un futuro flujo compensatorio enlazará las correcciones con el movimiento original; el campo `corrects` está reservado, pero no hay interfaz pública para ello.
