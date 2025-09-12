.PHONY: ingest
ingest:
	@echo "Starting data ingestion..."
	python qdrant_loader.py

.PHONY: duplicates
duplicates:
	@echo "Removing duplicate entries from Qdrant..."
	python qdrant_delete_duplicates.py

.PHONY: run
run:
	@echo "Running the FastAPI server..."
	uvicorn main:app --host 0.0.0.0 --port 8000 --reload

.PHONY: install
install:
	@echo "Installing dependencies..."
	pip install -r requirements.txt