import argparse
import tempfile
from pathlib import Path

from restore_ssid_content import restore_ssid_content
from restore_storyreasoning_content import restore_storyreasoning_content


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DATA_DIR = REPO_ROOT / "data"
MAPPING_DIR = DATA_DIR / "mappings"
DEFAULT_INPUT_JSON = DATA_DIR / "multivationbench.json"
DEFAULT_OUTPUT_JSON = DATA_DIR / "multivationbench_with_story.json"
DEFAULT_SSID_MAPPING = MAPPING_DIR / "ssid_mapping.json"
DEFAULT_STORYREASONING_MAPPING = MAPPING_DIR / "storyreasoning_mapping.json"


def generate_gt_with_story(
    input_json: Path,
    output_json: Path,
    ssid_mapping: Path,
    storyreasoning_mapping: Path,
):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "gt_after_ssid.json"

        restore_ssid_content(
            input_json=input_json,
            mapping_json=ssid_mapping,
            output_json=temp_path,
        )
        restore_storyreasoning_content(
            input_json=temp_path,
            mapping_json=storyreasoning_mapping,
            output_json=output_json,
        )

    print(f"Saved combined output: {output_json}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate multivationbench_with_story.json from the release-safe benchmark JSON."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_JSON,
        help="Input release-safe JSON. Default: data/multivationbench.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_JSON,
        help="Output JSON with restored story content. Default: data/multivationbench_with_story.json",
    )
    parser.add_argument(
        "--ssid-mapping",
        type=Path,
        default=DEFAULT_SSID_MAPPING,
        help="SSID mapping JSON.",
    )
    parser.add_argument(
        "--storyreasoning-mapping",
        type=Path,
        default=DEFAULT_STORYREASONING_MAPPING,
        help="StoryReasoning mapping JSON.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    generate_gt_with_story(
        input_json=args.input,
        output_json=args.output,
        ssid_mapping=args.ssid_mapping,
        storyreasoning_mapping=args.storyreasoning_mapping,
    )
