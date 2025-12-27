.PHONY: up down down-clean logs test

up:
	docker-compose -f docker-compose.yml -f docker-compose.ops.yml up -d --build

down:
	docker-compose -f docker-compose.yml -f docker-compose.ops.yml down

down-clean:
	docker-compose -f docker-compose.yml -f docker-compose.ops.yml down -v

logs:
	docker-compose -f docker-compose.yml -f docker-compose.ops.yml logs -f

test:
	docker-compose exec backend pytest
