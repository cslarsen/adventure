run:
	@python3 prowess.py

prepare:
	@python3 prepare.py

boot:
	python3 prepare.py > start.py
	python3 start.py
