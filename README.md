# Dataclass Config

## Overview

This is a small library to manage configuring python applications. It uses the dataclass functionality introduced in python 3.7
and attempts to make configuration consistent across development, production, and interactive coding environments. The core
features to enables this are:

- Loading from multiple sources, with automatic fallback
  - Runtime configuration
  - a configuration file defined in yaml
  - the environment variables of the system
  - defaults defined in the dataclass
- nested configurations
- type validation
- parsing string encoding of configuration variables based on introspection
- automating the namespacing of environment variables through introspection
