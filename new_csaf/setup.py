#!/usr/bin/env python

from distutils.core import setup

setup(name='new_csaf',
      version='1.0',
      description='Python Distribution Utilities',
      author='Greg Ward',
      author_email='gward@python.net',
      url='https://www.python.org/sigs/distutils-sig/',
      packages=['csaf','csaf.core','csaf.test', 'f16lib','f16lib.models','f16lib.models.helpers','f16lib.models.trained_models'],
     )
