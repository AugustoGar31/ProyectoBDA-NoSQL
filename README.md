# NexoSQL - Proyecto NoSQL

Proyecto académico de modelado y uso de MongoDB para una plataforma de
aprendizaje de SQL.

## Modelo de datos

El script crea tres colecciones:

- `modulos_sql`: módulos con docente titular y ejercicios embebidos. Cada
  ejercicio incluye una consigna, una solución SQL esperada y un puntaje.
- `usuarios`: estudiantes con comisión, fecha de registro y referencias a los
  módulos aprobados mediante `ObjectId`.
- `entregas_practicas`: entregas con referencias al estudiante y al módulo,
  consulta enviada, estado, tiempo de ejecución, intentos y revisión docente
  opcional.

Las entregas se mantienen en una colección independiente porque crecen con
cada intento y no deben ampliar indefinidamente los documentos de usuarios o
módulos.

## Requisitos

- Docker Desktop con Docker Compose.
- Python 3.10 o superior.
- Un entorno virtual de Python recomendado.

## Configuración

1. Crear el archivo local de variables:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Editar `.env` y establecer una contraseña propia. El archivo `.env` está
   ignorado por Git y no debe subirse al repositorio.

3. Crear y activar el entorno virtual:

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

## Ejecutar MongoDB y poblar datos

Iniciar el contenedor:

```powershell
docker compose up -d
```

Poblar la base:

```powershell
python seed.py
```

El script elimina y vuelve a crear las colecciones `modulos_sql`, `usuarios`
y `entregas_practicas` en cada ejecución. Es intencional para que la carga sea
reproducible.

MongoDB queda disponible desde el equipo host en `localhost:27018` y utiliza
autenticación contra la base `admin`.

Para detener el contenedor:

```powershell
docker compose down
```

Los datos locales se guardan en `mongo_data/`, que no se versiona en Git.

## Comandos útiles

```powershell
docker compose ps
docker compose logs -f mongodb
```

## Estructura principal

```text
.
├── docker-compose.yml
├── seed.py
├── requirements.txt
├── .env.example
├── Consigna_Proyecto_NoSQL_MongoDB.pdf
└── README.md
```
