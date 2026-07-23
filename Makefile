PYTHON ?= python

.PHONY: verify demo package release-check

verify:
	$(PYTHON) scripts/verify.py

demo:
	$(PYTHON) scripts/demo.py

package:
	$(PYTHON) scripts/package_release.py

release-check:
	$(PYTHON) scripts/release_check.py

