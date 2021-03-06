SRC=./src
TEST_SRC=./tests

.PHONY: run test

run:
	@cd $(SRC) && python3.10 main.py

test:
#	@echo '### mypy results ###'
#	@mypy --python-version=3.10 $(SRC)
#	@printf "\n### tests results ###\n"
	@export PYTHONPATH="$(PWD)/$(SRC)" \
	 && cd $(TEST_SRC) \
	 && python3.10 -m unittest discover -v .
