# Decisiones técnicas iniciales

## 1. Movimiento como historial y saldo como proyección

Los movimientos explican cada cambio y son auditables. El saldo separado permite que las pantallas consulten cantidades sin sumar todo el historial en cada solicitud. Como toda proyección puede desincronizarse, se define desde el inicio un camino para reconstruir y comparar.

## 2. Servicio de dominio compartido

La validación de stock no vive en una vista ni exclusivamente en un serializer. Un único servicio transaccional lo aplica para web, API, admin y comandos. El admin puede servir para tareas administrativas, pero no debe ofrecer edición directa del saldo ni de movimientos confirmados.

## 3. PostgreSQL como base objetivo

El control concurrente de salidas y las restricciones relacionales son centrales al problema. Las consultas y la puesta en producción deben ejercitarse contra PostgreSQL; SQLite puede facilitar prototipos locales, pero no demostrar estas garantías.

## 4. Ajustes con delta explícito

Un conteo físico produce una diferencia positiva o negativa respecto del saldo del sistema. Guardar ese delta permite entender qué cambió. La cantidad física contada y el saldo previo/resultante podrían añadirse al evento si durante la implementación se confirma que se necesitan para auditoría; no se duplican campos sin un requisito claro.

## 5. Archivado en vez de borrado

Productos, proveedores y ubicaciones con referencias históricas se desactivan. Así las consultas actuales pueden ocultar elementos archivados y los movimientos antiguos siguen siendo legibles.

## 6. Alcance de una organización

El MVP modela una sola empresa por instalación para evitar complejidad prematura de aislamiento de datos. Antes de ofrecerlo a varias empresas en una misma instancia habrá que introducir organización y comprobar que cada consulta queda acotada por ella.

## 7. API versionada desde el inicio

La API REST usa `/api/v1/`, aunque sea consumida por la propia interfaz al principio. Mantiene un contrato claro y permite añadir clientes sin acoplar el dominio a una página concreta.

## Pendiente de decidir antes del primer sprint

- Si cada usuario podrá ver costos/precios de compra o solo cantidades.
- Si cantidades fraccionarias son requisito real.
- Si el despliegue inicial será AWS, según el objetivo y presupuesto disponibles.
- Si una salida requiere referencia externa (venta, orden o centro de costo).
