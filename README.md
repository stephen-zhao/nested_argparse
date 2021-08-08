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

## API Documentation

The library exposes the following modules.

### Module `nested_argparse`

The module exports the following classes.

#### Class `NestedArgumentParser`

- extends `argparser.ArgumentParser`
- for documentation for the superclass, see the official [Python API reference docs for `argparse`](https://docs.python.org/3/library/argparse.html).

##### Constructor

In addition to the parameters available to `ArgumentParser` constructor, the following parameters are also accepted:

- Param `nest_dir`, optional, type: `Optional[str]`
  - When a string is passed in, it is used as the attribute name in the parent namespace to which the nested namespace, where the parsed values will be stored, is assigned to.
  - When `None` is passed in, no nested namespace is created, and parsed values are directly assigned to the parent namespace. This is the behavior of the base `ArgumentParser`.
  - Default value: `None`.

- Param `nest_separator`, optional, type: `str`
  - It is used as the separator to delimit components in the nest path when representing the path as a string (for example, this is used to generate `dest`s)
  - Default value: `'__'`.

- Param `nest_path`, optional, type: `Optional[List[str]]`
  - When a list of strings is passed in, it is used as a sequence of nested attribute names from the parent namespace which locates the nested namespace where the parsed values will be stored.
  - When `None` is passed in, no nested namespace is created, and parsed values are directly assigned to the parent namespace. This is the behavior of the base `ArgumentParser`.
  
##### Override `NestedArgumentParser.add_argument`

Instead of adding an argument definition which stores the parsed value to `dest` in the flat top-level namespace, the parsed value will be stored at attribute with the name given by `dest` in the namesapce at the nesting path associated with this parser.

##### Override `NestedArgumentParser.add_subparsers`

The return value of this method is an instance of internal subparser handler `_NestedSubParsersAction`, which exposes extra options for adding subparsers.

##### Override `NestedArgumentParser.parse_args`

The return value of this method is a namespace tree rather than a flat namespace. The tree is built according to the nesting paths associated with each of the parsed values.

##### Override `NestedArgumentParser.parse_known_args`

The return value of this method is a namespace tree rather than a flat namespace. The tree is built according to the nesting paths associated with each of the parsed values.

#### Class `_NestedSubParsersAction`

##### Override `_NestedSubParsersAction.add_parser`

- Param `nest_dir`, optional, type: `Optional[str]`
  - When a string is passed in, it is used as the attribute name in the parent namespace to which the subparser will store its parsed values to.
  - When `None` is passed in, the `dest` field is used as the nesting directory instead.
  - Default value: `None`.
