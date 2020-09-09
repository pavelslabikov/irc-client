import argparse
from client import Client
from configparser import ConfigParser

if __name__ == "__main__":
    config = ConfigParser(allow_no_value=True)
    config.read("config.ini")
    client = Client(config)
    client.start_client()
