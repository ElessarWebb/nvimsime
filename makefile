
mkenv:
	virtualenv .virtualenv

install:
	test -d .virtualenv || ${MAKE} mkenv
	. .virtualenv/bin/activate; pip install -r requirements
