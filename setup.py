from setuptools import setup

version = '0.0.1'

with open('requirements.txt', 'r') as f:
    install_reqs = [
        s for s in [
            line.strip(' \n') for line in f
        ] if not s.startswith('#') and s != ''
    ]


test_requirements = (
    'nose',
    'flake8',
    'coverage',
    'mypy',
    'asynctest'
)

setup(name='feed-transformer',
      version=version,
      description='goodreads-feed-transformer',
      url='https://github.com/b1r3k/goodreads-feed-transformer',
      packages=['transformer'],
      classifiers=[
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.6',
          'Operating System :: POSIX',
      ],
      install_requires=install_reqs,
      extras_require={
          'dev': test_requirements
      },
      entry_points={
          'paste.app_factory': ['app = transformer:app'],
      })
