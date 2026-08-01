.PHONY: volume postgres init api app all

# Crea un volumen de Docker para persistir los datos de la base de datos
volume:
	docker volume create anime

# Ejecuta la base de datos PostgreSQL en un contenedor Docker usando el volumen
postgres: volume
	docker run -d \
	--name postgres \
	-e POSTGRES_DB=anime_assistant \
	-e POSTGRES_USER=user \
	-e POSTGRES_PASSWORD=password \
	-v anime:/var/lib/postgresql/data \
	-p 5432:5432 \
	postgres:17

# Crea las tablas de la base de datos y las puebla con los archivos CSV
init: 
	python db_init.py

# Ejecuta la API
api: 
	uv run api.py

# Ejecuta la aplicación de Streamlit (la API debe iniciarse antes)
app: 
	uv run streamlit run app.py

# Comando para ejecutar todo el flujo en cadena
all: app