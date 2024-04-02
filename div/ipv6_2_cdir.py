#!/usr/bin/env python3
#
import sys
import os
import argparse
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
import Libraries.tools.general as gt

def run():
    description = 'Converts list of IPV6 addresses into /64 cdirs, eleminates dupes'
    parser = argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
                                     description = description)

    parser.add_argument('input_file', nargs=1, help='Input file with IPV6 addresses - REQUIRED')

    args = parser.parse_args()

    result = []
    with open(args.input_file[0], 'rt') as fd:
        for line in fd:
            if line.find(':') != -1:
                a = line.split(':')[0:4]
                a.append('')
                a.append('/64')
                result.append(':'.join(a))

        result = gt.unique(result)

        for element in result:
            print(element)

if __name__ == '__main__':
    run()
