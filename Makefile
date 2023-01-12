build:
	docker build -t mirror:dev .

run:
	docker run --env-file=.env -it --rm -p 19500:80 mirror:dev
