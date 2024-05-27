import os

import typing

import yaml
import json


class ConfigLoadException(Exception):
    pass


class BaseConfig():
    __frozen = False
    __env_root: str | None = None

    def __init__(self, _freeze: bool=True, _env_root: str | None=None, **kwargs):

        if _env_root is None:
            self.__env_root = self.__class__.__module__
        else:
            self.__env_root = _env_root

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

        print(f_type)
        t_origin = typing.get_origin(f_type)
        t_args = typing.get_args(f_type)

        if t_origin is None:  # we have a base type
            if issubclass(f_type, BaseConfig):
                if isinstance(v, str):
                    v = json.loads(v)

                if not isinstance(v, dict):
                    raise ConfigLoadException(f"Attemping to load {f_type} but found {v}")

                new_env_root = self.__env_root + '_' + k
                
                v = f_type.from_dict(v, _env_root=new_env_root, _freeze=self.__freeze)
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
            elif t_origin is list:
                v = v.split(',')
                r_f_type = t_args[0]
                v = [self.__parse_value(r_f_type, k, item.strip()) for item in v]

        return v
    
    def __get_from_env(self, k: str):

        v = None

        # first, try the env var with full env root
        if self.__env_root is not None:
            env_k = (self.__env_root + '_' + k).upper()
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
                print(f"{getattr(self, field)} != {getattr(other, field)}")
                return False

        return True
    
    @classmethod
    def from_dict(cls, data, **kwargs):
        
        return cls(**data, **kwargs)
    
    @classmethod
    def from_file(cls, file):
        with open(file, 'r') as fp:
            data = yaml.load(fp.read(), Loader=yaml.Loader)
        
        return cls.from_dict(data)