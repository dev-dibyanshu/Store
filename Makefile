.PHONY: start stop logs ingest clean deploy build

start:
	@echo "🚀 Starting Store Intelligence MVP..."
	docker-compose up -d
	@sleep 5
	@echo "✅ Ready! Dashboard: http://localhost:3000 | API: http://localhost:8000/docs"

stop:
	docker-compose down

logs:
	docker-compose logs -f

ingest:
	@echo "📥 Loading sample data..."
	@sleep 2
	@curl -X POST http://localhost:8000/ingest
	@echo "\n✅ Data loaded!"

ingest-cv:
	@echo "📥 Loading CV-generated events..."
	@sleep 2
	@curl -X POST http://localhost:8000/ingest-cv
	@echo "\n✅ CV data loaded!"

clean:
	docker-compose down -v
	rm -rf data/store.db

build:
	@echo "🔨 Building Docker images..."
	docker-compose build

deploy:
	@echo "🚀 Deploying to production..."
	./deploy.sh

demo: start ingest-cv
	@echo "🎉 Demo ready! Opening dashboard..."
	@sleep 3
	@open http://localhost:3000 || xdg-open http://localhost:3000
