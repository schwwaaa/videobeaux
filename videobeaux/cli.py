import os
import sys
import shutil
import math
import argparse
import importlib
from pathlib import Path
from pyfiglet import Figlet

from videobeaux.utils.vb_argparser import VB_Program_ArgParser

def main():
    a = Figlet(font='ogre')
    print(a.renderText("videobeaux"))
    print("📺 The friendly multilateral video toolkit built for artists by artists. ")
    print("🫂  It's your best friend!")
    print()
    print("🌐 schwwaaa")

    #print('-' * 50)
    print()

    # global parser
    parser = argparse.ArgumentParser(
        #description="",
        usage="videobeaux --program PROGRAM --input INPUT_FILE --output OUTPUT_FILE [program options]",
        add_help=False, # handling help manually - see below
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-P", "--program", help="Name of the effect program to run (e.g. convert, glitch)")
    parser.add_argument("-i", "--input", help="Input video file - mp4 only")
    parser.add_argument("-o", "--output", help="Output file name, no extension. Output will be saved as mp4.")
    #parser.add_argument("-c", "--config", help="Optional config file")
    parser.add_argument("-F", "--force", action="store_true", help="Force overwrite output file")
    parser.add_argument("-h", "--help", action="store_true", help="Show help message and exit")

    global_args, remaining = parser.parse_known_args()

    # Validate and sanitize output filename
    # TODO - revist MP4 only
    if global_args.output:
        output_path = Path(global_args.output)
        suffix = output_path.suffix.lower()

        if suffix and suffix != ".mp4":
            print(f"❌ Invalid file extension.  --output accepts a file name, which will be saved as mp4.")
            sys.exit(1)
        if not suffix:
            global_args.output += ".mp4"


    # gloabl --help
    def print_columns(items, padding=2):
        items = sorted(items)
        terminal_width = shutil.get_terminal_size().columns
        max_len = max(map(len, items)) + padding
        cols = max(1, terminal_width // max_len)
        rows = math.ceil(len(items) / cols)
        for row in range(rows):
            line = ''.join(
                items[col * rows + row].ljust(max_len)
                for col in range(cols)
                if col * rows + row < len(items)
            )
            print(line)

    parser.print_help()
    print()
    if global_args.help and not global_args.program:
        program_dir = os.path.join(os.path.dirname(__file__), "programs")  

        available_programs = sorted([
            f[:-3] for f in os.listdir(program_dir)
            if f.endswith(".py") and not f.startswith("_")
        ])

        print("Available Program Modes: \n")
        print_columns(available_programs)
        print()
        sys.exit(0)

    # program load
    if not global_args.program:
        print("❌ You must specify a --program.")
        parser.print_help()
        sys.exit(1)
    try:
        mod = importlib.import_module(f"videobeaux.programs.{global_args.program}")
        print(f"Selected program mode: {global_args.program}")

    except ModuleNotFoundError as e:
        print(f"❌ Program '{global_args.program}' not found in videobeaux.programs. ({e.name})")
        sys.exit(1)

    program_parser = VB_Program_ArgParser(
        prog=f"{parser.prog} --program {global_args.program}",
        description=f"🔧 Arguments for program '{global_args.program}'",
        formatter_class=argparse.RawTextHelpFormatter
    )
    mod.register_arguments(program_parser)


    # program --help
    if global_args.help:
        parser.print_help()
        print("\n 👁️ 👇 Additional help for program mode 👇 👁️")
        program_parser.print_help()
        sys.exit(0)

    program_args = program_parser.parse_args(remaining)
    if global_args.input and not Path(global_args.input).exists():
        print(f"❌ {global_args.input} doesn't exists. WTF?")
        sys.exit(1)

    if global_args.output and not global_args.force and Path(global_args.output).exists():
        print(f"❌ {global_args.output} already exists. Use --force to overwrite.")
        sys.exit(1)

    # combined_args = argparse.Namespace(**vars(global_args), **vars(program_args))
    # try:
    #     mod.run(combined_args)
    # except:
    #     print(f"😵 Exiting due to failure...")
    #     sys.exit(1)
    combined_args = argparse.Namespace(**vars(global_args), **vars(program_args))
    try:
        mod.run(combined_args)
    except Exception as e:
        import traceback
        print("\n💥 Program crashed with an unhandled exception:\n")
        traceback.print_exc()
        print("\n🐛 Combined args that were passed to the program:\n", combined_args)
        print("\n😵 Exiting due to failure...")
        sys.exit(1)    

if __name__ == "__main__":
    main()
