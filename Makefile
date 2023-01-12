build:
	docker build -t mirror:latest .

run-api:
	API_COMPONENT=api docker-compose up

run-crawler:
	API_COMPONENT=crawler-daemon docker-compose up
