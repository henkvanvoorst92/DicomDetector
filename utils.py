
import os
import pandas as pd
from tqdm import tqdm
import argparse
import yaml

def combine_excel_files(p_dir, incl_string='.xlsx', verbose=False):
    if verbose:
        return pd.concat([pd.read_excel(os.path.join(p_dir, f)) for f in tqdm(os.listdir(p_dir)) if incl_string in f], axis=0)
    else:
        return pd.concat([pd.read_excel(os.path.join(p_dir, f)) for f in os.listdir(p_dir) if incl_string in f], axis=0)


def get_general_args(args=None):
    parser = argparse.ArgumentParser(
        description="General image processing pipeline"
    )

    # Input/output
    parser.add_argument(
        "-i", "--input",
        required=False,
        help="Input file(s) or directory"
    )
    parser.add_argument(
        "-o", "--output",
        required=False,
        help="Output file or directory"
    )

    parser.add_argument(
        "-j", "--njobs",
        required=False,
        default=1,
        type=int,
        help="NUmber of jobs to run in parallel"
    )

    parser.add_argument(
        "-yml", "--yml_args",
        required=False,
        default=None,
        type=str,
        help="YAML file with arguments"
    )

    args = parser.parse_args(args)
    if args.yml_args is not None:
        yml_args = load_yaml_config(args.yml_args)
        update_args_with_yaml(args, yml_args)

    return args

