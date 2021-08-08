from src.nested_argparse import NestedArgumentParser

def test_multinesting():
  subparser_3 = NestedArgumentParser()
  subparser_3.add_argument('--level', type=int, default=3)
  subparser_3.add_argument('--some_flag')
  subparser_2 = NestedArgumentParser()
  subparser_2.add_argument('--level', type=int, default=2)
  subparser_2.add_argument('--some_flag')
  subparser_2.add_subparsers(dest='sub').add_parser('sub_3', parents=[subparser_3], add_help=False)
  subparser_1 = NestedArgumentParser()
  subparser_1.add_argument('--level', type=int, default=1)
  subparser_1.add_argument('--some_flag')
  subparser_1.add_subparsers(dest='sub').add_parser('sub_2', parents=[subparser_2], add_help=False)
  main_parser = NestedArgumentParser()
  main_parser.add_argument('--level', type=int, default=0)
  main_parser.add_argument('--some_flag')
  main_parser.add_subparsers(dest='sub').add_parser('sub_1', parents=[subparser_1], add_help=False)
  

  # Run the parser on test argv
  test_argv = ['--some_flag=A', 'sub_1', '--some_flag=B', 'sub_2', '--some_flag=C', 'sub_3', '--some_flag=D']
  args = main_parser.parse_args(test_argv)
  
  assert 'some_flag' in args and args.some_flag == 'A'
  assert 'level' in args and args.level == 0
  assert 'sub' in args and args.sub == 'sub_1'
  assert 'sub_1' in args

  assert 'some_flag' in args.sub_1 and args.sub_1.some_flag == 'B'
  assert 'level' in args.sub_1 and args.sub_1.level == 1
  assert 'sub' in args.sub_1 and args.sub_1.sub == 'sub_2'
  assert 'sub_2' in args.sub_1

  assert 'some_flag' in args.sub_1.sub_2 and args.sub_1.sub_2.some_flag == 'C'
  assert 'level' in args.sub_1.sub_2 and args.sub_1.sub_2.level == 2
  assert 'sub' in args.sub_1.sub_2 and args.sub_1.sub_2.sub == 'sub_3'
  assert 'sub_3' in args.sub_1.sub_2

  assert 'some_flag' in args.sub_1.sub_2.sub_3 and args.sub_1.sub_2.sub_3.some_flag == 'D'
  assert 'level' in args.sub_1.sub_2.sub_3 and args.sub_1.sub_2.sub_3.level == 3
