#!/usr/bin/env python

from distutils.core import setup

setup(name='new_csaf',
      version='1.1',
      description='New CSAF no ZMQ with hack for cloudpickle, ray',
      author='GaloisInc',
      author_email='',
      url='https://github.com/yokian/csaf',
      packages=['csaf','csaf.core','csaf.test', 'f16lib','f16lib.models','f16lib.models.helpers','f16lib.models.trained_models'],
     )
