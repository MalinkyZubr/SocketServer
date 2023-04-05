import argparse


parser = argparse.ArgumentParser(prog=__name__)
parser.add_argument("-v")

print(tuple(vars(parser.parse_args()).keys()))
