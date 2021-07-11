# coding=utf-8

"""
This file is the entrypoint of the project.
"""

import argparse

from h4r_parser import H4ResourceFile
from settings import data_dir

# This holds [text, mpvies, updates, heroes4, music] but there could be some other files in the future.
files_name = [k for k in data_dir.keys()]

# Will hold parsed data as an H4ResourceFile object
files = dict()


def parse_file(name):
    """
    Instanciates the objects we are gonna work on.
    """
    files[name] = H4ResourceFile(data_dir[name], name)


def extract_all(*args, **kwargs):
    for name in files_name:
        extract(name)


def extract(arguments, *args, **kwargs):
    try:
        # We are coming from the entrypoint,
        name = arguments.filename
    except AttributeError:
        # We are calling from extract_all.
        name = arguments
    try:
        # extract_all_files is poorly named, it extract all files of a single H4ResourceFile.
        files[name].extract_all_files(write_mp3=True)
    except KeyError as e:
        parse_file(name)
        files[name].extract_all_files(write_mp3=True)


parser = argparse.ArgumentParser(
    prog="heroes4-parser", description="Extract, transform, manipulates Heroes4 resources."
)

subparsers = parser.add_subparsers(help="commands")

# extractall command.
extractall_parser = subparsers.add_parser("extractall", help="Extract all files from all h4r files.")
extractall_parser.set_defaults(func=extract_all)

# extract command.
extract_parser = subparsers.add_parser("extract", help="Extract all files from the specified h4r file.")
extract_parser.add_argument("filename", type=str, choices=set(files_name), help="The file to extract.")
extract_parser.set_defaults(func=extract)

parser.add_argument("--version", action="version", version="%(prog)s-1.0")
arguments = parser.parse_args()
arguments.func(arguments)
