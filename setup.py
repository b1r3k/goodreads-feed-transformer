from setuptools import setup

version = '0.0.1'

with open('requirements.txt', 'r') as f:
    install_reqs = [
        s for s in [
            line.strip(' \n') for line in f
        ] if not s.startswith('#') and s != ''
    ]

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
      install_reqs=install_reqs,
      entry_points={
          'paste.app_factory': ['app = transformer:app'],
      })
