# custom_parser.py
import argparse
import sys

class VB_Program_ArgParser(argparse.ArgumentParser):
    def error(self, message):
        if "the following arguments are required" in message:
            self.print_help(sys.stderr)
            print(f"\n❌ Missing required argument(s): {message.split(':', 1)[1].strip()}")
            sys.exit(2)
        else:
            super().error(message)
