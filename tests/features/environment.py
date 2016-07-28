# copyright notices and license terms.
# The COPYRIGHT file at the top level of this repository contains the full
import os
import time

# from trytond.config import config
from proteus import config as pconfig
from trytond import backend

# Set Database
if backend.name() == 'sqlite':
    database_name = ':memory:'
else:
    database_name = 'test_' + str(int(time.time()))
os.environ.setdefault('DB_NAME', database_name)


from trytond.tests.test_tryton import doctest_teardown, \
    install_module


def before_all(context):
    context.config.setup_logging()
    print('Backend:', backend.name())
    install_module('contract')
    context._proteus_config = pconfig.set_trytond()


def after_all(context):
    print("DROP DB:", database_name)
    doctest_teardown(database_name)


# These run before and after a section tagged with the given name.
# They are invoked for each tag encountered in the order theyâ€™re
# found in the feature file. See controlling things with tags.
def before_tag(context, tag):
    pass


def after_tag(context, tag):
    pass


# These run before and after each feature file is exercised.
def before_feature(context, feature):
    pass


def after_feature(context, feature):
    pass


# These run before and after each scenario is run.
def before_scenario(context, scenario):
    pass


def after_scenario(context, scenario):
    pass


# These run before and after every step.
def before_step(context, step):
    pass


def after_step(context, step):
    pass
