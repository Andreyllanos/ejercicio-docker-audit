# Auditoría Técnica y de Seguridad

## Ejercicio Docker Audit

| Campo | Detalle |
|---|---|
| Fecha de entrega | 2026-09-04 |
| Repositorio | `ejercicio-docker-audit` |
| Entorno de ejecución | AWS EC2 sobre Ubuntu |
| Orquestación | Docker Engine y Docker Compose |
| Herramienta SAST | Bandit 1.9.4 |
| Estado | Despliegue operativo y documentado |

## 1. Resumen Ejecutivo

El proyecto implementa un entorno de aplicación contenerizado desplegado en una instancia AWS EC2 con Ubuntu. Docker Compose coordina el backend de la aplicación, la base de datos y las herramientas de operación y observabilidad.

Los servicios levantados son:

- `app-backend`: API desarrollada con Flask.
- `servidor-bd`: base de datos MySQL 8.0 con persistencia mediante volumen Docker.
- `uptime-kuma`: supervisión de disponibilidad y estado de los servicios.
- `dozzle`: consulta y seguimiento en tiempo real de los logs de los contenedores.

El acceso externo se centraliza mediante Nginx, instalado en el host Ubuntu y configurado como Reverse Proxy. Los bloques `server` enrutan subdominios personalizados bajo `*.duckdns.org` hacia los servicios correspondientes, evitando exponer directamente la topología interna de la aplicación al usuario final.

## 2. Arquitectura y Componentes del Sistema

### 2.1 Topología lógica

Los cuatro contenedores se conectan a la red bridge de Docker Compose `app-network`:

```text
Internet
	|
	v
Nginx en Ubuntu (80)
	|
	+--> app-backend (5050) ----+
	|                           |
	+--> uptime-kuma (3001)     +--> app-network
	|                           |
	+--> dozzle (8080) ---------+
										 |
										 +--> servidor-bd (MySQL 8.0, interno)
```

La aplicación utiliza el nombre de servicio `db` para resolver la base de datos dentro de la red Docker. MySQL no publica un puerto al host, por lo que solo es accesible desde los servicios conectados a `app-network`.

### 2.2 Componentes y puertos

| Componente | Contenedor | Puerto interno | Publicación en el host | Función |
|---|---|---:|---:|---|
| API Flask | `app-backend` | 5050 | 5050 | Exposición de la aplicación backend |
| MySQL 8.0 | `servidor-bd` | 3306 | No publicado | Persistencia de datos de la aplicación |
| Uptime Kuma | `uptime-kuma` | 3001 | 3001 | Monitoreo de disponibilidad |
| Dozzle | `dozzle` | 8080 | 8080 | Visualización de logs Docker |
| Reverse Proxy | Nginx en Ubuntu | 80 | 80 | Enrutamiento por subdominio |

Los datos de MySQL se conservan en el volumen `db_data` y los datos de Uptime Kuma en `kuma_data`. Los contenedores tienen política `restart: always` y el backend depende del healthcheck de MySQL antes de iniciar.

## 3. Problemas Críticos Identificados y Soluciones Aplicadas

### 3.1 Incompatibilidad de versiones Python/Flask

La combinación inicial de versiones de Python, Flask, Jinja2, MarkupSafe, itsdangerous y Werkzeug podía provocar errores de importación y fallos al iniciar la aplicación. El problema se resolvió fijando explícitamente versiones compatibles en el `Dockerfile`:

```text
Flask==1.1.2
PyMySQL==0.9.3
Jinja2==2.11.3
MarkupSafe==1.1.1
itsdangerous==2.0.1
Werkzeug==2.0.3
cryptography==3.4.8
```

El pinning reduce la variabilidad entre reconstrucciones de la imagen y permite reproducir el entorno utilizado durante la entrega.

### 3.2 Autenticación con MySQL 8.0

MySQL 8.0 utiliza `caching_sha2_password` como mecanismo de autenticación predeterminado. La dependencia `cryptography==3.4.8` se incorporó para proporcionar el soporte criptográfico requerido por PyMySQL y evitar errores de conexión durante la autenticación.

### 3.3 Gestión de nombres y red

Se establecieron nombres explícitos para los contenedores (`app-backend`, `servidor-bd`, `uptime-kuma` y `dozzle`) y una red común `app-network`. Esto evita ambigüedades durante la operación y permite que el backend resuelva la base de datos mediante el nombre de servicio `db`.

La configuración también previene conflictos de red al mantener la comunicación entre servicios dentro de la red bridge administrada por Compose y separar el acceso externo, gestionado por Nginx.

## 4. Configuración de Infraestructura y Producción

### 4.1 Nginx y subdominios

Nginx se instaló y configuró en el sistema Ubuntu de la instancia EC2. Cada bloque `server` recibe solicitudes para un subdominio DuckDNS y las reenvía al puerto publicado del servicio correspondiente:

| Subdominio lógico | Destino interno |
|---|---|
| API (`api.<dominio>.duckdns.org`) | `127.0.0.1:5050` |
| Monitoreo (`monitor.<dominio>.duckdns.org`) | `127.0.0.1:3001` |
| Logs (`logs.<dominio>.duckdns.org`) | `127.0.0.1:8080` |

La terminación y las reglas de acceso se concentran en el Reverse Proxy, mientras que Docker conserva la separación funcional de los servicios. Los nombres concretos de los subdominios dependen del dominio DuckDNS asignado a la instancia.

### 4.2 Grupos de seguridad de AWS

Se verificaron las reglas de entrada del Security Group asociado a la instancia EC2. La configuración operativa contempla:

| Puerto | Protocolo | Uso | Criterio de exposición |
|---:|---|---|---|
| 80 | TCP | Nginx / HTTP | Público para el acceso web y el proxy |
| 22 | TCP | SSH | Restringido a las IP o rangos administrativos autorizados |
| 3001 | TCP | Uptime Kuma | Solo si se requiere acceso directo; preferentemente detrás de Nginx |
| 5050 | TCP | API Flask | Solo si se requiere acceso directo; preferentemente detrás de Nginx |
| 8080 | TCP | Dozzle | Solo si se requiere acceso directo; preferentemente detrás de Nginx |

El puerto 3306 de MySQL no debe exponerse públicamente y permanece sin publicación en Docker Compose. Como medida de endurecimiento, los puertos 3001, 5050 y 8080 deben limitarse a la red administrativa o cerrarse cuando el acceso se realice exclusivamente a través de Nginx.

## 5. Monitoreo y Auditoría en Tiempo Real

### 5.1 Dozzle

Dozzle se integra mediante el socket de Docker y proporciona una interfaz web para consultar los logs de los contenedores en tiempo real. Esta capacidad facilita:

- Diagnosticar errores de arranque y conexión con MySQL.
- Correlacionar eventos entre el backend y los servicios auxiliares.
- Verificar reinicios provocados por la política `restart: always`.

El acceso a Dozzle debe protegerse mediante Nginx, controles de acceso y reglas de red administrativas, ya que los logs pueden contener información operativa sensible.

### 5.2 Uptime Kuma

Uptime Kuma monitoriza la disponibilidad de los endpoints publicados y permite detectar interrupciones del backend, del proxy o de los servicios operativos. Su volumen `kuma_data` conserva la configuración de monitores y el histórico disponible dentro del despliegue.

Se recomienda configurar comprobaciones HTTP para la API y para cada subdominio publicado, además de alertas por correo o por el canal operativo elegido.

## 6. Auditoría SAST y Riesgos de Seguridad

La revisión inicial con Bandit 1.9.4 identificó los siguientes puntos en la aplicación:

| ID | Archivo | Hallazgo | Severidad | Confianza | Tratamiento |
|---|---|---|---|---|---|
| BANDIT-01 | `app.py` | Credencial de base de datos potencialmente expuesta | Baja | Media | Gestionar secretos mediante `.env` fuera del repositorio y variables protegidas de despliegue |
| BANDIT-02 | `app.py` | Posible inyección SQL por concatenación | Media | Baja | Usar consultas parametrizadas y validar entradas antes de enviarlas a MySQL |
| BANDIT-03 | `app.py` | Modo debug o binding inseguro | Alta | Media | Desactivar debug en producción y mantener el binding en `0.0.0.0` únicamente dentro del contenedor, con acceso externo controlado por Nginx |

Estos hallazgos deben permanecer en el ciclo de remediación hasta contar con una nueva ejecución de Bandit que confirme su cierre. El archivo `bandit_auditoria.txt` conserva el resultado detallado de la ejecución utilizada como referencia.

## 7. Conclusión y Recomendaciones

El despliegue final presenta una separación clara entre aplicación, persistencia, monitoreo y observabilidad. La red de Compose, los healthchecks, los volúmenes persistentes, el pinning de dependencias y el Reverse Proxy permiten una operación reproducible y administrable en AWS EC2.

Como acciones de mejora se recomienda:

1. Mantener las credenciales exclusivamente en secretos de despliegue y rotarlas periódicamente.
2. Cerrar o restringir los puertos directos de los contenedores cuando Nginx sea el único punto de entrada.
3. Ejecutar Bandit y pruebas automatizadas en cada cambio de código o imagen.
4. Fijar también las versiones de las imágenes Docker y revisar periódicamente vulnerabilidades de base.
5. Habilitar HTTPS con certificados válidos para los subdominios DuckDNS y aplicar autenticación a las interfaces administrativas de Dozzle y Uptime Kuma.