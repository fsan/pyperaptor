include $(shell bash .mkdkr init)

python.3.6:
	@$(dkr)
	instance: python:3.6
	run: python test_pyperaptor.py

python.3.7:
	@$(dkr)
	instance: python:3.7
	run: python test_pyperaptor.py

python.3.8:
	@$(dkr)
	instance: python:3.8
	run: python test_pyperaptor.py

python.latest:
	@$(dkr)
	instance: python:latest
	run: python test_pyperaptor.py
