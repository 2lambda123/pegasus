import os
import sys
from unittest import TestLoader, TestSuite, TextTestRunner

# The service only works on python >= 2.5
if sys.version_info >= (2,5):
    test_service = True
else:
    test_service = False

# Try to import the dependencies to make sure they exist
try:
    import Pegasus
    import sqlalchemy
    if test_service:
        import sqlite3
        import boto
        import requests
        import flask
        import Pegasus.service
    else:
        import pysqlite2
except ImportError, e:
    print e
    print "Unable to import Pegasus modules"
    print "Make sure dependencies are available"
    print "Set PYTHONPATH or run: python setup.py develop"
    sys.exit(1)

def discoverTestModules(dirpath):
    modules = []
    for name in os.listdir(dirpath):
        path = os.path.join(dirpath, name)
        if os.path.isdir(path):
            modules += discoverTestModules(path)
        elif name.endswith(".py") and name.startswith("test_"):
            modules.append(path.replace(".py", "").replace("/", "."))
    return modules

loader = TestLoader()
alltests = TestSuite()

for module in discoverTestModules("Pegasus/test"):
    # If not testing service, skip service test modules
    if not test_service and module.startswith("Pegasus.test.service"):
        continue
    suite = loader.loadTestsFromName(module)
    alltests.addTest(suite)

runner = TextTestRunner(verbosity=2)
result = runner.run(alltests)

if result.wasSuccessful():
    sys.exit(0)
else:
    sys.exit(1)

