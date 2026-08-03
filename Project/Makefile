.PHONY: volume postgres init api app grafana all

# Crea un volumen de Docker para persistir los datos de la base de datos
volume:
	docker volume create anime
	docker volume create grafana_data

volume_rm:
	docker volume rm project_grafana_data
	docker volume rm project_anime
	
	

# Ejecuta la base de datos PostgreSQL en un contenedor Docker usando el volumen
postgres: volume
	docker run --rm \
	 -d \
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

grafana:
	docker run --rm -d \
	--name grafana \
	-e "GF_SECURITY_ADMIN_PASSWORD=admin" \
	-e "GF_SECURITY_ADMIN_USER=admin" \
	-p 3000:3000 \
	-v grafana_data:/var/lib/grafana \
	grafana/grafana:13.1.0

# Comando para ejecutar todo el flujo en cadena
all: app
