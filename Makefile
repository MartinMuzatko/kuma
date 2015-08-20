# Note: these targets should be run from the kuma vm
django-tests:
	python manage.py test

performance-tests:
	locust -f tests/load/smoke.py --host=https://developer.allizom.org

# Note: this target should be run from the host machine with selenium running
browser-tests:
	pushd tests/ui ; ./node_modules/.bin/intern-runner config=intern-local d=developer.allizom.org b=firefox; popd