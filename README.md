# nested-argparse 💬 → 🅰.🅱.🆒

[![PyPI](https://img.shields.io/pypi/v/nested-argparse?color=brightgreen&label=pypi%20package)](https://pypi.org/project/nested-argparse/)
![PyPI - Status](https://img.shields.io/pypi/status/nested-argparse)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/nested-argparse)
[![PyPI - License](https://img.shields.io/pypi/l/nested-argparse)](https://github.com/stephen-zhao/nested_argparse/blob/main/LICENSE)

nested-argparse is a python module that non-invasively builds on top of the built-in `argparse` library to allow subparsers to parse into their own nested namespaces.

The library exposes a class `NestedArgumentParser` which allows arbitrary nesting without worry of namespace conflicts. This is achieved with the following principles of this library:

- **Inversion of Control:** A parser, when adding a subparser, is in control of what name to use for the sub-namespace which the subparser sends its parsed args to.
- **Drop-In Replacement:** The constructor for `nested_argparse.NestedArgumentParser` can be substituted in directly to where the constructor for `argparse.ArgumentParser` is being used. All subsequent method calls and subparser API calls should work without any additional code change!
- **Customizeability:** There are additional `kwargs` exposed to further customize the nesting options to your liking, if the defaults do not suit your scenario.

The main difference between this library and its built-in counterpart is the return value of the `parse_args` method. Instead of a flat namespace containing all parsed arguments across all subparsers, `NestedArgumentParser` will produce a namespace tree.

## Simple Conceptual Example

Given the following parser:

```
Root Parser
 ├─ positional_1
 ├─ --optional_1
 ├─ --optional_2
 └─ sub parsers with dest='subcommand'
     ├─ Sub Parser 1 with name='sub1'
     │   ├─ --optional_1
     │   └─ --optional_2 with dest='optional2AltName'
     └─ Sub Parser 2 with name='sub2'
         ├─ --optional_1
         └─ --optional_2
```

And the following args to parse:

```sh
Alice --optional_1=Bob sub1 --optional_1=Carol --optional_2=David
```

The built-in `ArgumentParser` would not be able to handle the duplication in `dest`s, but `NestedArgumentParser` will produce the following result when run through `parse_args`:

```py
Namespace(
  subcommand='sub1',
  positional_1='Alice',
  optional_1='Bob',
  sub1=Namespace(
    optional_1='Carol',
    optional2AltName='David'
  )
)
```