.PHONY: test
test:
	poetry run pytest --cov=moneyloverc --cov-report=html
