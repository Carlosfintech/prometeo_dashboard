.PHONY: gen-model migrate seed test-ml test-metrics test-clients test-all all

gen-model:
	python models/create_dummy_model.py

migrate:
	alembic upgrade head

seed:
	python -m scripts.seed_data

test-ml:
	PYTHONPATH=. pytest tests/test_ml.py -v

test-metrics:
	PYTHONPATH=. pytest tests/test_metrics.py -v

test-clients:
	PYTHONPATH=. pytest tests/test_mock_db.py -v

test-all: test-ml test-metrics test-clients

all: gen-model seed test-all 