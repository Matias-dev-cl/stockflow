# Revisión funcional — 18 de octubre de 2026

## Hallazgos corregidos

| Hallazgo | Corrección |
|---|---|
| Logout sin página de destino | Redirige al login |
| .env documentado pero no cargado | Carga explícita desde la raíz del proyecto |
| URL de base de datos inválida podía terminar en SQLite | Falla con error de configuración |
| Credenciales con caracteres escapados en URL | Decodificación al construir la conexión |
| Ajustes negativos con signo duplicado | Signo y color derivados del efecto real |
| Historial limitado a las últimas filas | Paginación en web y API |
| Catálogo sin edición completa accesible | Formulario autorizado y acceso desde lista/detalle |
| Cambiar la unidad podía reinterpretar cantidades históricas | Unidad bloqueada y validada después del primer movimiento |
| Archivado sin flujo de usuario | Archivar/reactivar conservando saldo e historial |
| Enlaces históricos podían fallar al archivar | Detalles archivados siguen accesibles |
| Falta de restricciones de tipo/cantidad en base | Nueva migración con constraint |
| Motivo vacío o desbordamiento desde servicio | Validación central de motivo, autor y rango |
| Datos demo escribían saldo e historial por separado | Usa el mismo servicio, dentro de una transacción |
| Controles visuales sin función y curvas de tendencia sin datos | Eliminados; guía real dentro de la aplicación |
| Texto pequeño y catálogo ancho en móvil | Tamaños legibles y tarjetas de productos |
| Documentación describía módulos/tablas aún inexistentes | Ajustada al código real y a pendientes explícitos |

## Validación

- Suite automatizada de 37 pruebas: 36 aprobadas en SQLite y una prueba concurrente omitida por requerir bloqueo de fila.
- Controles de Django, ausencia de migraciones pendientes y compatibilidad de dependencias.
- Revisión visual en navegador de resumen, catálogo, formulario de edición y guía.
- Los tests usan una base temporal; no alteran los datos de demostración del usuario.
- Workflow de GitHub Actions preparado con PostgreSQL 16. No se ha ejecutado en GitHub: el repositorio sigue local.
- Docker está instalado, pero su motor no está iniciado en este equipo. No se presenta la prueba concurrente como validada localmente.

## Trabajo pendiente conocido

| Trabajo | Estado |
|---|---|
| Validar concurrencia con PostgreSQL | Prueba escrita; pendiente de ejecución en ese motor |
| Subir repositorio y ejecutar CI | Workflow preparado; pendiente de publicar el repositorio |
| Despliegue público, HTTPS, estáticos y respaldos | Pendiente |
| Varias relaciones producto–proveedor y códigos externos | Pendiente; hoy hay un proveedor principal |
| OpenAPI y edición REST del catálogo | Pendiente; API inicial documentada en README |
| Correcciones enlazadas al movimiento original | Pendiente; ajustes simples ya funcionan |
| Gestión de categorías/proveedores/ubicaciones fuera del admin | Pendiente; hoy se administran en Django |

Esta revisión verifica el funcionamiento local y las reglas cubiertas por pruebas. La preparación de producción y las extensiones anteriores requieren trabajo adicional.
