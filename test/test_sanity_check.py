from src.nested_argparse import NestedArgumentParser

def test_sanity_check():
  # Create a subparser as a standalone parser first
  drink_parser = NestedArgumentParser()
  drink_parser.add_argument('--speed', default='fast', choices=['fast', 'slow', 'MEGA'])

  # Create the main parser
  main_parser = NestedArgumentParser(prog='boba')
  main_parser.add_argument('--with-tapioca', action='store_true', dest='hasTapioca')
  main_parser.add_argument('--sugar-level', type=int, default=75)

  # Add subparsers to the main parser
  subparser_adder = main_parser.add_subparsers(dest='command', required=True)
  
  # Add the existing "drink" parser as a subparser
  drink_subparser = subparser_adder.add_parser('drink', parents=[drink_parser], add_help=False)
  drink_subparser.add_argument('--amount', type=int, required=True)

  # Add a new "make" subparser
  make_subparser = subparser_adder.add_parser('make')
  make_subparser.add_argument('--with-tapioca', action='store_true', dest='hasTapioca')
  make_subparser.add_argument('--sugar-level', type=int, default=100)

  # Run the parser on test argv
  test_argv = ['--with-tapioca', 'make', '--with-tapioca', '--sugar-level', '25']
  args = main_parser.parse_args(test_argv)
  
  assert 'boba' in args
  assert 'hasTapioca' in args.boba and args.boba.hasTapioca == True
  assert 'sugar_level' in args.boba and args.boba.sugar_level == 75
  assert 'command' in args.boba and args.boba.command == 'make'
  assert 'make' in args.boba
  assert 'hasTapioca' in args.boba.make and args.boba.make.hasTapioca == True
  assert 'sugar_level' in args.boba.make and args.boba.make.sugar_level == 25