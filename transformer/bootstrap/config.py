import yaml
import collections
import os

from .log import setup_logging


def get_config(config_path, args_config=None):
    config_dict = dict(
        config_path=config_path
    )
    if args_config:
        config_dict.update(vars(args_config))
    config_path = config_dict['config_path']
    with open(config_path, 'rt') as f:
        print(f'Loading config from: {config_path}')
        yaml_config = yaml.safe_load(f.read())
        yaml_config.update(config_dict)
    # overwrite with env variables!
    for option in yaml_config.keys():
        env_name = f'{yaml_config["app_name"].upper()}_{option.upper()}'
        env = os.environ.get(env_name)
        if env:
            print(f'Overriding {option} via env variable {env_name}')
            yaml_config[option] = env
    Config = collections.namedtuple("Config", yaml_config.keys())
    config = Config(**yaml_config)
    logging_cfg = getattr(config, 'logging', None)
    setup_logging(logging_cfg)
    return config
