import os
import argparse
import mlray.cli.generate_config as generate_config
from dotenv import load_dotenv

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.yml')

def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Manage Ray Serve config.yml based on MLflow registry.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_config_parser = subparsers.add_parser("generate-config", help="Generate Ray Serve config from MLflow model registry")
    generate_config.configure_paser(generate_config_parser)

    args = parser.parse_args()
    args_dict = vars(args).copy()
    for key in ['command', 'main']:
        del args_dict[key]
    args.main(**args_dict)
