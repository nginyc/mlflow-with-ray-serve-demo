import os
import argparse
import mlray.cli.update_config as update_config
from dotenv import load_dotenv

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.yml')

def main():
    parser = argparse.ArgumentParser(description="Manage Ray Serve config.yml based on MLflow registry.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    update_config_parser = subparsers.add_parser("update-config", help="Update the Ray Serve config.yml based on the ML model registry")
    update_config.configure_paser(update_config_parser)

    args = parser.parse_args()
    args_dict = vars(args).copy()
    for key in ['command', 'main']:
        del args_dict[key]
    args.main(**args_dict)

if __name__ == "__main__":
    load_dotenv()
    main()
