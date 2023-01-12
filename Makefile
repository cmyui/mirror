build:
	docker build -t mirror:latest .

run-api:
	APP_COMPONENT=api docker-compose up

run-crawler:
	APP_COMPONENT=crawler-daemon docker-compose up
