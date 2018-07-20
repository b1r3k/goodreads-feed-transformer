from setuptools import setup

version = '0.0.1'

setup(name='feed-transformer',
      version=version,
      description='goodreads-feed-transformer',
      url='https://www.getkeepsafe.com/',
      packages=['transformer'],
      classifiers=[
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.6',
          'Operating System :: POSIX',
      ],
      entry_points={
          'paste.app_factory': ['app = transformer:app'],
      })
