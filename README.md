# Stacked Config

## Overview

This is a small library to manage configuring python applications. It started as a desire to explore the type annotation
functionality added to python, and build a consistent and flexible means of defining configurations.

Features:
- Loading from multiple sources, with automatic fallback
  - Runtime configuration
  - a configuration file defined in yaml
  - the environment variables of the system
  - defaults defined in the dataclass
- nested configurations
- type validation
- parsing string encoding of configuration variables based on introspection
- automating the optional namespacing of environment variables through introspection
