# Auditoría Técnica y de Seguridad - Ejercicio Docker Audit

- **Fecha:** 2026-09-04
- **Repositorio:** `ejercicio-docker-audit`
- **Herramienta SAST:** Bandit 1.9.4

## Tabla de Hallazgos (Bandit)

| ID | Archivo | Línea | Hallazgo | Severidad | Confianza | Estado |
|----|---------|------:|----------|-----------|-----------|--------|
| BANDIT-01 | `app.py` | 10 | Contraseña de base de datos expuesta | Baja | Media | Pendiente |
| BANDIT-02 | `app.py` | 25 | Inyección SQL potencial por concatenación | Media | Baja | Pendiente |
| BANDIT-03 | `app.py` | - | Modo debug activo / binding inseguro | Alta | Media | Pendiente |

*Nota: Puedes abrir tu archivo `bandit_auditoria.txt` con el comando `cat bandit_auditoria.txt` en la terminal si deseas detallar las líneas exactas que arrojó tu ejecución local.*