
import os
import pandas as pd
from tqdm import tqdm
import argparse
import yaml

def combine_excel_files(p_dir, incl_string='.xlsx', verbose=False):
    if verbose:
        return pd.concat([pd.read_excel(os.path.join(p_dir, f)) for f in tqdm(os.listdir(p_dir)) if incl_string in f and os.path.exists(os.path.join(p_dir, f)) and not 'lock' in f], axis=0)
    else:
        return pd.concat([pd.read_excel(os.path.join(p_dir, f)) for f in os.listdir(p_dir) if incl_string in f and os.path.exists(os.path.join(p_dir, f)) and not 'lock' in f], axis=0)

def write_excel_chunks(df, max_len, file="output", index=False):
    max_len = int(max_len)
    for i in tqdm(range(0, len(df), max_len), desc=f"Writing {file} in chunks of {max_len} rows"):
        df.iloc[i:i + max_len].to_excel(
            f"{file}_{i // max_len + 1}.xlsx",
            index=index
        )

def load_yaml_config(yaml_file):
    with open(yaml_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

def update_args_with_yaml(args, yaml_config):
    if args is None:
        args = argparse.Namespace()

    for key, value in yaml_config.items():
        if isinstance(value, dict):
            # Store the entire dictionary as an attribute
            setattr(args, key, value)
            # Also flatten nested dictionary keys
            for sub_key, sub_value in value.items():
                arg_key = f"{key}_{sub_key}"
                setattr(args, arg_key, sub_value)
        else:
            setattr(args, key, value)
    return args

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

def make_columns_unique(columns):
    seen = {}
    new_cols = []

    for col in columns:
        if col not in seen:
            seen[col] = 0
            new_cols.append(col)
        else:
            seen[col] += 1
            new_cols.append(f"{col}_{seen[col]}")

    return new_cols