build:
	docker build -t mirror:latest .

# run:
# 	docker run --env-file=.env -it --rm -p 19500:80 mirror:dev

run:
	docker-compose up
