.PHONY: test test-saas test-api help

help:
	@echo "make test-saas  run SaaS test suite"
	@echo "make test-api   run IVS test suite"
	@echo "make test       both"

test-saas:
	$(MAKE) -C saas test

test-api:
	$(MAKE) -C api test

test: test-api test-saas
