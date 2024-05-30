import os

import typing

import yaml
import json

import logging

logger = logging.getLogger(__name__)


class ConfigLoadException(Exception):
    pass


class BaseConfig():
    __frozen = False
    __env_prefix: str | None = None

    def __init__(self, _freeze: bool=True, _env_prefix: str | None=None, **kwargs):

        if _env_prefix is None:
            self.__env_prefix = self.__class__.__module__
        else:
            self.__env_prefix = _env_prefix

        self.__freeze = _freeze

        for k, v in kwargs.items():
            if k not in self.__annotations__:
                raise TypeError(f"{self.__class__}.__init__() found and unexpected keyword argument '{k}'")
            
            f_type = typing.get_type_hints(self)[k]

            v = self.__parse_value(f_type, k, v)
            
            setattr(self, k, v)

        for k in self.__annotations__:
            if k not in kwargs:
                v = self.__get_from_env(k)
                if v is not None:
                    setattr(self, k, v)

        self.__frozen = self.__freeze

    def __parse_value(self, f_type: typing.Type, k: str, v: typing.Any):

        t_origin = typing.get_origin(f_type)
        t_args = typing.get_args(f_type)

        if t_origin is None:  # we have a base type
            if issubclass(f_type, BaseConfig):
                if isinstance(v, str):
                    v = json.loads(v)

                if not isinstance(v, dict):
                    raise ConfigLoadException(f"Attemping to load {f_type} but found {v}")

                new_env_prefix = self.__env_prefix + '_' + k
                logger.debug(f"Loading child config of type {f_type} and _env_prefix={new_env_prefix}")
                
                v = f_type.from_dict(v, _env_root=new_env_prefix, _freeze=self.__freeze)

        elif t_origin is typing.Union:
            if len(t_args) > 2 or type(None) not in t_args:
                raise TypeError(f'Only Optional[] is supported found Union{repr(list(t_args))}')
            
            r_f_type = next(iter(filter(lambda x: x is not type(None), t_args)))
            v = self.__parse_value(r_f_type, k, v)

        if f_type is not str and isinstance(v, str):
            if f_type in (int, float):
                v = f_type(v)

            elif f_type is dict:
                v = json.loads(v)

            elif f_type is bool:
                valid_bool = ('True', 'true', 'False', 'false')
                if v not in valid_bool:
                    raise TypeError(f"Expected {valid_bool} but got '{v}'")
                v = v in ('True', 'true')

            elif t_origin is list:
                v = v.split(',')
                r_f_type = t_args[0]
                v = [self.__parse_value(r_f_type, k, item.strip()) for item in v]

            else:
                raise TypeError(f"Unsupported string parsing for type: {f_type}")

        return v
    
    def __get_from_env(self, k: str):

        v = None

        # first, try the env var with full env root
        if self.__env_prefix is not None:
            env_k = (self.__env_prefix + '_' + k).upper()
            v = os.environ.get(env_k)
            
        if v is None:
            # next, try the derivative case of just the field key
            env_k = k.upper()
            v = os.environ.get(env_k)

        # if haven't found anything we can return it
        if v is None:
            return v
        
        # if we have any comp
        f_type = typing.get_type_hints(self)[k]
        return self.__parse_value(f_type, k, v)

    def __setattr__(self, name: str, value: typing.Any) -> None:
        if self.__frozen:
            raise TypeError(f"{self.__class__} objet is frozen does not support item assignment")
        
        self.__dict__[name] = value

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        
        for field in self.__annotations__:
            if getattr(self, field, None) != getattr(other, field, None):
                return False

        return True
    
    def __repr__(self):
        r = f"{self.__class__.__module__}.{self.__class__.__name__}("
        r += ', '.join([f"{f}={repr(getattr(self, f))}" for f in self.__annotations__])
        r += ')'
        return r
    
    @classmethod
    def from_dict(cls, data, _freeze=True, _env_prefix=None):
        
        return cls(**data, _freeze=_freeze, _env_prefix=_env_prefix)
    
    @classmethod
    def from_file(cls, file, _freeze=True, _env_prefix=None, **override_values):
        with open(file, 'r') as fp:
            data = yaml.load(fp.read(), Loader=yaml.Loader)

        if override_values:
            data.update(override_values)
        
        return cls.from_dict(data, _freeze=_freeze, _env_prefix=_env_prefix)