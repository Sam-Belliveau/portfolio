from __future__ import annotations

import argparse
import time
from pathlib import Path

from bevelkit import load_config, write_tiles


def report(name, pass_name, index, total):
    print(f"\r  {name}: {pass_name} {index}/{total}   ", end="", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Render bevel 9-slice tiles")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--quiet", action="store_true")
    arguments = parser.parse_args()

    config = load_config(arguments.config)
    started = time.time()
    stylesheet = write_tiles(config, progress=None if arguments.quiet else report)
    print(f"\rwrote {stylesheet} in {time.time() - started:.1f}s" + " " * 24)


if __name__ == "__main__":
    main()
