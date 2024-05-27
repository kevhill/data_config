from data_config import BaseConfig

from typing import Optional, List

import pathlib
import yaml
import os

import pytest

os.environ['LOAD_FROM_ENV'] = '1'
os.environ['LIST_OF_STR'] = 'a,b, c'
os.environ['LIST_OF_FLOAT'] = '0.5, 0.7, 0'
os.environ['INNER_FROM_ENV'] = '{"test_str": "a", "test_int": 1}'
os.environ['OVERLOAD_FROM_ENV'] = 'OVERLOAD_FAILED'
os.environ['TEST_DATA_CONFIG_OVERLOAD_FROM_ENV'] = 'OVERLOAD_SUCCESS'
os.environ['TEST_DATA_CONFIG_INNER_CONFIG_OVERLOAD_FROM_ENV'] = 'INNER_OVERLOAD_SUCCESS'

test_dir = pathlib.Path(__file__).parent


class ConfigInner(BaseConfig):
    test_str: str
    test_int: int
    list_of_str: List[str]
    list_of_float: List[float]
    overload_from_env: str


class ConfigSimple(BaseConfig):
    test_str: str
    test_int: int


class ConfigTest(BaseConfig):
    inner_config: ConfigInner
    simple_str: str
    default_value: int = 1
    load_from_env: Optional[int] = None
    overload_from_env: str
    list_str: List[str]
    inner_from_env: ConfigSimple


class TestLoad:

    test_dict = {
        'inner_config': {
            'test_str': 'success',
            'test_int': 1,
        },
        'simple_str': 'success',
        'list_str': ['a', 'b']
    }

    def test_init(self):

        config = ConfigTest(**self.test_dict)

        # Basic data types
        assert config.simple_str == self.test_dict['simple_str']

        # default objects should be frozen
        with pytest.raises(TypeError):
            config.simple_str = 'foo'

        # Nested Configs and equality
        inner_config = ConfigInner(**self.test_dict['inner_config'], _env_root='TEST_DATA_CONFIG_INNER_CONFIG')
        assert config.inner_config == inner_config

        # Test inequality
        other_inner_config = ConfigInner(test_str='other', test_int=0)
        assert config.inner_config != other_inner_config

        # Test default values work.
        assert config.default_value == 1

        # Test that we got things read from env
        assert config.load_from_env == 1

        # Test that we can also not parse env strings
        assert config.inner_config.list_of_str == ['a', 'b', 'c']
        assert config.inner_config.list_of_float == [0.5, 0.7, 0.0]
        assert config.inner_from_env == ConfigSimple(test_str='a', test_int=1)

        # Test preference for specific env vars
        assert config.overload_from_env == 'OVERLOAD_SUCCESS'
        assert config.inner_config.overload_from_env == 'INNER_OVERLOAD_SUCCESS'

    def test_unfrozen(self):
        config = ConfigInner(**self.test_dict['inner_config'], _freeze=False)
        config.test_str = 'modified!'

        assert config.test_str == 'modified!'

    def test_from_dict(self):

        config = ConfigTest.from_dict(self.test_dict)
        test_inner = ConfigInner.from_dict(self.test_dict['inner_config'])

        assert config.inner_config == test_inner

    def test_from_file(self):

        test_file = test_dir.joinpath('test_config.yaml')

        with open(test_file, 'r') as fp:
            target_config = yaml.load(fp.read(), Loader=yaml.Loader)

        config = ConfigTest.from_file(test_file)
        test_inner = ConfigInner.from_dict(target_config['inner_config'])
        assert config.inner_config == test_inner
