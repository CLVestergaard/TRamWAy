#!/usr/bin/env python

from tramway.core import *
from tramway.core.hdf5 import *
import pandas as pd


def merge_analyses(analysis_trees, into=0):
    if isinstance(into, Analyses):
        analysis_tree = into
        copy = False
    else:
        copy = into is None or into < 0
        analysis_tree = analysis_trees.pop(0 if copy else into)
    if copy:
        raise NotImplementedError('selected analysis tree can only be modified in-place')
    def df_equal(node, other_node):
        if node.type is pd.DataFrame and not other_node.data.equals(node.data):
            raise ValueError('location data differ between trees')
    merge_any_level(analysis_tree, analysis_trees, df_equal)
    return analysis_tree


def merge_rwa(input_files, output_file, force=False, **kwargs):
    if not (input_files and input_files[1:]):
        raise ValueError('too few input files')
    if len(set(input_files)) < len(input_files):
        raise ValueError('duplicate input files')
    overwrite = output_file in input_files
    lazy = not overwrite
    analysis_trees = [ load_rwa(_file, lazy=lazy) for _file in input_files ]
    assert all( isinstance(tree, Analyses) for tree in analysis_trees )
    merged_tree = merge_analyses(analysis_trees, **kwargs)
    save_rwa(output_file, merged_tree, force=force or overwrite)


def main():
    import argparse
    try:
        from ConfigParser import ConfigParser
    except ImportError:
        from configparser import ConfigParser
    parser = argparse.ArgumentParser(prog='merge',
        description='Combine several rwa files into a single analysis tree.')
    parser.add_argument('--overwrite', '--force', action='store_true', help='overwrite output file if it already exists')
    parser.add_argument('output_file', help='output file')
    parser.add_argument('input_files', nargs=argparse.REMAINDER, help='list of input files')
    args = parser.parse_args()
    merge_rwa(args.input_files, args.output_file, force=args.overwrite)


if __name__ == '__main__':
    main()

