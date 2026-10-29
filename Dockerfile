# Imagen base liviana oficial de Python
FROM python:3.11-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar dependencias e instalarlas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente necesario de la API
COPY src/main.py src/repository.py ./src/

# Exponer el puerto de FastAPI
EXPOSE 8000

# Comando para iniciar la API escuchando en todas las interfaces de red del contenedor
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
