"""Download the Kaggle dataset used to train the gesture classifier.

Requires the Kaggle CLI and an API token:

    pip install kaggle
    # place your token at  ~/.kaggle/kaggle.json

Then run:

    python tools/download_data.py
    python tools/download_data.py --dataset <owner/dataset-name>
"""

import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gesture_control import config  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Download a Kaggle hand-gesture dataset.")
    parser.add_argument("--dataset", default=config.DEFAULT_KAGGLE_DATASET,
                        help="Kaggle dataset slug, e.g. owner/dataset-name")
    parser.add_argument("--out", default=config.RAW_DATA_DIR, help="Destination directory")
    args = parser.parse_args()

    try:
        import kaggle  # noqa: F401
    except ImportError:
        print("The Kaggle CLI is not installed. Install it with:  pip install kaggle")
        return 1

    token = os.path.expanduser(os.path.join("~", ".kaggle", "kaggle.json"))
    if not os.path.exists(token):
        print("No Kaggle API token found at {}".format(token))
        print("Create one at https://www.kaggle.com/settings -> API -> Create New Token,")
        print("then save the downloaded kaggle.json to that path.")
        return 1

    os.makedirs(args.out, exist_ok=True)
    cmd = ["kaggle", "datasets", "download", "-d", args.dataset, "-p", args.out, "--unzip"]
    print("Running:", " ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    sys.exit(main())
