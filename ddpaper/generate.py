from __future__ import print_function

import sys
import argparse
from ddpaper.data import setup_yaml
from ddpaper.render import get_latex_jinja_env
from ddpaper.filters import setup_custom_filters
from ddpaper.data import load_data_directory, load_data_ddobject
from ddpaper.render import render_definitions, render_draft, extract_referenced_keys

try:
    from dataanalysis import core
    dda_available=True
except ImportError:
    print("WARNING: no DDA")
    dda_available=False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input",default="main.tex")
    parser.add_argument("output",default="definitions.tex")
    parser.add_argument("-d","--data",default="./data")
    parser.add_argument("--draft",action='store_true',default=False)
    parser.add_argument('-a', dest='assume', metavar='ASSUME', type=str, help='...', nargs='+', action='append',
                        default=[])
    parser.add_argument('-m', dest='modules', metavar='MODULE_NAME', type=str, help='module to load', nargs='+',
                        action='append', default=[])
    parser.add_argument('-l', dest='load', metavar='LOAD', type=str, help='...', nargs='+', action='append',
                        default=[])
    parser.add_argument("-w","--write-caches", dest="writecaches", action='store_true', default=False)


    args=parser.parse_args()

    if args.writecaches and dda_available:
        core.global_readonly_caches = False

    latex_jinja_env=get_latex_jinja_env()
    setup_custom_filters(latex_jinja_env)

    setup_yaml()

    data=load_data_directory(args.data)
    data=load_data_ddobject(args.modules,args.assume,args.load,data)

    if args.draft:
        render_draft(latex_jinja_env,
                           data,
                           args.input,
                           output_filename=args.output)
    else:
        render_definitions(latex_jinja_env,
                           extract_referenced_keys(args.input),
                           data,
                           output_filename=args.output)

if __name__ == '__main__':
    main()
