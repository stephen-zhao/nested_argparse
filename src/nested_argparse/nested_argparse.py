import argparse
from typing import Any, Dict, List, Optional, Tuple

DEBUG=False

def _debug_log(*args):
  if DEBUG:
    print(*args)

class NestedArgumentParser(argparse.ArgumentParser):
  def __init__(self,
               prog=None,
               nest_dir=None,
               nest_separator='__',
               nest_path=None,
               usage=None,
               description=None,
               epilog=None,
               parents=[],
               formatter_class=argparse.HelpFormatter,
               prefix_chars='-',
               fromfile_prefix_chars=None,
               argument_default=None,
               conflict_handler='error',
               add_help=True,
               allow_abbrev=True):

    # Determine the nest path of this parser
    if nest_path is None:
      if nest_dir is not None:
        nest_components = [nest_dir]
      else:
        nest_components = []
    else:
        nest_components = nest_path

    # Save the nest path and related config
    self.nest_dir: Optional[str] = nest_components[-1] if len(nest_components) > 0 else None
    self.nest_path_components: List[str] = nest_components
    self.nest_separator: str = nest_separator

    # Mapping from nested dest back to the original dest for contained Actions
    self._original_dest_by_nested_dest = {}

    superinit = super(NestedArgumentParser, self).__init__
    superinit(prog=prog,
              usage=usage,
              description=description,
              epilog=epilog,
              parents=parents,
              formatter_class=formatter_class,
              prefix_chars=prefix_chars,
              fromfile_prefix_chars=fromfile_prefix_chars,
              argument_default=argument_default,
              conflict_handler=conflict_handler,
              add_help=add_help,
              allow_abbrev=allow_abbrev)

    # Override the subparsers action to use the Nested edition
    self.register('action', 'parsers', _NestedSubParsersAction)

  # ==================================
  # Optional/Positional adding methods
  # ==================================

  def add_subparsers(self, **kwargs):
    if 'dest' in kwargs:
      # Extract dest from kwargs
      dest = kwargs['dest']

      # Get the nested dest
      nested_dest = self._get_nested_dest_and_save_original(dest.replace('-', '_'))

      # Override the dest with the nested dest
      kwargs['dest'] = nested_dest
      
    # Add base nest path details so the subparsers action will know which nest to extend from
    kwargs['base_nest_path'] = self.nest_path_components
    kwargs['nest_separator'] = self.nest_separator

    return super().add_subparsers(**kwargs)

  # =====================================
  # Command line argument parsing methods
  # =====================================
  
  def parse_known_args(self, args=None, namespace=None) -> Tuple[argparse.Namespace, List[str]]:
    _debug_log('IN override parse_known_args given args=', args, '; namespace=', namespace)
    parsed_args, unknown_args = super().parse_known_args(args=args, namespace=namespace)
    deflattened_args = self._deflatten_namespace(parsed_args)
    _debug_log('OUT override parse_known_args deflattened_args=', deflattened_args, '; unknown_args=', unknown_args)
    return deflattened_args, unknown_args

  # ==================================
  # Namespace default accessor methods
  # ==================================

  def set_defaults(self, **kwargs: Any) -> None:
    nested_dests = {}
    for dest, value in kwargs.items():
      nested_dest = self._get_nested_dest_and_save_original(dest)
      nested_dests[nested_dest] = value
    return super().set_defaults(**nested_dests)
  
  def get_default(self, dest: str) -> Any:
    nested_dest = self._get_nested_dest(dest)
    return super().get_default(nested_dest)
    
  # ==================================
  # Internal methods
  # ==================================

  def _deflatten_namespace(self, namespace: argparse.Namespace) -> argparse.Namespace:
    _debug_log('deflattening..........')
    root_namespace = argparse.Namespace()
    # Loop through all attributes in the original namespace
    for key, value in vars(namespace).items():
      _debug_log('key=', key, '; value=', value)
      components = key.split(self.nest_separator)
      # Start at the root namespace
      curr_namespace = root_namespace
      # Loop through all ancestor components
      for component in components[0:-1]:
        # Create a namespace in the current namespace if not already present
        if component not in curr_namespace:
          setattr(curr_namespace, component, argparse.Namespace())
        # Move on to the child component and child namespace
        curr_namespace = getattr(curr_namespace, component)
      # We are now at the destination namespace for the value to be added
      # Check if a value already exists
      if hasattr(curr_namespace, components[-1]):
        existing_value = getattr(curr_namespace, components[-1])
        # Check if both existing and new values are namespaces, in which case we actually need to recursively merge
        if isinstance(existing_value, argparse.Namespace) and isinstance(value, argparse.Namespace):
          self._recursively_merge_namespaces(existing_value, value)
        else:
          raise ValueError(f'Cannot merge namespaces due to conflict at key "{key}".')
      else:
        setattr(curr_namespace, components[-1], value)
      _debug_log(root_namespace)
    return root_namespace

  def _recursively_merge_namespaces(self, dest_namespace: argparse.Namespace, src_namespace: argparse.Namespace) -> argparse.Namespace:
    _debug_log('both are namespaces, so recursively merge:')
    _debug_log('    merge destination:', dest_namespace)
    _debug_log('    merge source:', src_namespace)
    for attr, src_value in vars(src_namespace).items():
      # Check if destination has attribute with same name
      if hasattr(dest_namespace, attr):
        dest_value = getattr(dest_namespace, attr)
        # Check if both are namespaces, in which case we can recursively merge
        if isinstance(dest_value, argparse.Namespace) and isinstance(src_value, argparse.Namespace):
          _debug_log('    --> both', attr, 'are namespaces, so setting', attr, 'by merging')
          setattr(dest_namespace, attr, self._recursively_merge_namespaces(dest_value, src_value))
        else:
          raise ValueError(f'Cannot merge namespaces due to conflict at attribute "{attr}".')
      else:
        _debug_log('    --> no', attr, 'yet, so setting', attr, '=', src_value)
        setattr(dest_namespace, attr, src_value)
    return dest_namespace

  def _add_container_actions(self, container: argparse._ActionsContainer) -> None:
    self._remap_container_dests(container)
    return super()._add_container_actions(container)

  def _remap_container_dests(self, container: argparse._ActionsContainer) -> None:
    _debug_log('remapping container', container)
    original_defaults = container._defaults
    nested_defaults = { self._get_nested_dest(dest): value for dest, value in original_defaults.items() }
    _debug_log('    remapping defaults', original_defaults)
    _debug_log('                    ->', nested_defaults)
    container._defaults = nested_defaults
    for action in container._actions:
      self._remap_action_dest(action)

  def _remap_action_dest(self, action: argparse.Action) -> None:
    _debug_log('    remapping action', action)
    if action.dest is not None:
      original_dest = action.dest
      nested_dest = self._get_nested_dest_and_save_original(original_dest)
      _debug_log('    ...', original_dest)
      _debug_log('     ->', nested_dest)
      action.dest = nested_dest
    if isinstance(action, _NestedSubParsersAction) and action.choices is not None:
      for _, subparser in action.choices.items():
        if isinstance(subparser, NestedArgumentParser):
          self._remap_container_dests(subparser)

  def _get_positional_kwargs(self, dest: str, **kwargs: Any) -> Dict[str, Any]:
    # Get the nested dest
    nested_dest = self._get_nested_dest_and_save_original(dest.replace('-', '_'))

    # Amend the other arguments with the original dest
    kwargs = self._amend_arguments(dest, **kwargs)

    return super()._get_positional_kwargs(nested_dest, **kwargs)
  
  def _get_optional_kwargs(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
    # Extract dest from args and kwargs
    dest = self._extract_dest(*args, **kwargs)

    # Get the nested dest
    nested_dest = self._get_nested_dest_and_save_original(dest.replace('-', '_'))
    
    # Override the dest with the nested dest
    kwargs['dest'] = nested_dest

    # Amend the other arguments with the original dest
    kwargs = self._amend_arguments(dest, **kwargs)

    return super()._get_optional_kwargs(*args, **kwargs)

  def _extract_dest(self, *args, **kwargs) -> str:
    if 'dest' in kwargs and kwargs['dest'] is not None:
      return kwargs['dest']

    # Otherwise, figure out what the dest should be first using the options args
    first_long_option_string = None
    first_short_option_string = None
    for option_string in args:
      if first_long_option_string:
        break
      elif not first_long_option_string and self._is_long_option_string(option_string):
        first_long_option_string = option_string
      elif not first_short_option_string and self._is_short_option_string(option_string):
        first_short_option_string = option_string
      
    if first_long_option_string:
      dest_option_string = first_long_option_string
    else:
      dest_option_string = first_short_option_string
  
    return dest_option_string.lstrip(self.prefix_chars)

  def _is_long_option_string(self, option_string: str) -> bool:
    return len(option_string) > 2 and option_string[0] in self.prefix_chars and option_string[1] in self.prefix_chars
  
  def _is_short_option_string(self, option_string: str) -> bool:
    return len(option_string) > 1 and option_string[0] in self.prefix_chars and option_string[1] not in self.prefix_chars

  def _get_nested_dest(self, dest: str) -> str:
    if self.nest_path_components is None or len(self.nest_path_components) == 0:
      return dest
    else:
      return self.nest_separator.join(self.nest_path_components) + self.nest_separator + dest

  def _get_nested_dest_and_save_original(self, dest: str) -> str:
    nested_dest = self._get_nested_dest(dest)
    self._original_dest_by_nested_dest[nested_dest] = dest
    return nested_dest

  def _amend_arguments(self, original_dest: str, **kwargs: Any) -> Any:
    if ('action' not in kwargs or kwargs['action'] == 'store'):
      if 'metavar' not in kwargs:
        kwargs['metavar'] = original_dest.upper()
    return kwargs

class _NestedSubParsersAction(argparse._SubParsersAction):
  def __init__(self,
               option_strings,
               prog,
               base_nest_path,
               nest_separator,
               parser_class=NestedArgumentParser,
               dest=argparse.SUPPRESS,
               required=False,
               help=None,
               metavar=None) -> None:
    superinit = super(_NestedSubParsersAction, self).__init__
    superinit(option_strings,
              prog,
              parser_class,
              dest=dest,
              required=required,
              help=help,
              metavar=metavar)

    self.base_nest_path_components = base_nest_path
    self.nest_separator = nest_separator

  def add_parser(self, name: str, **kwargs: Any) -> NestedArgumentParser:
    if 'nest_dir' in kwargs:
      nest_dir = kwargs['nest_dir']
    else:
      nest_dir = name
    kwargs['nest_path'] = self.base_nest_path_components + [nest_dir]
    kwargs['nest_separator'] = self.nest_separator
    return super().add_parser(name, **kwargs)
