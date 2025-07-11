import os
import argparse
import mlray.cli.deploy as deploy
from dotenv import load_dotenv

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.yml')

def main():
    parser = argparse.ArgumentParser(description="Manage Ray Serve config.yml based on MLflow registry.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    deploy_parser = subparsers.add_parser("deploy", help="Deploy models to Ray Serve based on the MLflow model registry")
    deploy.configure_paser(deploy_parser)

    args = parser.parse_args()
    args_dict = vars(args).copy()
    for key in ['command', 'main']:
        del args_dict[key]
    args.main(**args_dict)

if __name__ == "__main__":
    load_dotenv()
    main()
