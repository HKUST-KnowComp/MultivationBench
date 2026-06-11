import argparse
import json
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
DATA_DIR = REPO_ROOT / "data"
DEFAULT_INPUT_JSON = DATA_DIR / "multivationbench.json"
DEFAULT_MAPPING_JSON = DATA_DIR / "mappings" / "ssid_mapping.json"
DEFAULT_OUTPUT_JSON = DATA_DIR / "multivationbench.ssid_restored.json"
SSID_SPLIT_FILES = [
    REPO_ROOT / "Datasets" / "SSID" / "SSID_Train.json",
    REPO_ROOT / "Datasets" / "SSID" / "SSID_Test.json",
    REPO_ROOT / "Datasets" / "SSID" / "SSID_Validation.json",
]
SSID_IMAGE_DIR = REPO_ROOT / "Datasets" / "SSID" / "SSID_Images"


def load_upstream_ssid():
    stories = {}

    for split_path in SSID_SPLIT_FILES:
        if not split_path.exists():
            raise FileNotFoundError(
                f"Missing SSID annotation file: {split_path}. "
                "Download SSID_Annotations first and place the JSON files in Datasets/SSID/."
            )

        with split_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)

        for sublist in data.get("annotations", []):
            for annotation in sublist:
                story_id = str(annotation["story_id"])
                stories.setdefault(story_id, []).append(annotation)

    for story_id, annotations in stories.items():
        annotations.sort(key=lambda item: int(item["image_order"]))

    return stories


def rebuild_story_text(upstream_story):
    rebuilt = []

    for annotation in upstream_story:
        image_id = str(annotation["youtube_image_id"])
        image_path = Path("Datasets") / "SSID" / "SSID_Images" / f"{image_id}.jpg"
        local_image_path = SSID_IMAGE_DIR / f"{image_id}.jpg"
        if not local_image_path.exists():
            raise FileNotFoundError(
                f"Missing SSID image: {local_image_path}. "
                "Download SSID_Images and place them in Datasets/SSID/SSID_Images/."
            )

        rebuilt.append(
            {
                "image_order": int(annotation["image_order"]),
                "text": annotation.get("storytext", "").strip(),
                "image_path": image_path.as_posix(),
            }
        )

    return rebuilt


def apply_text_overrides(story_text, overrides):
    if not overrides:
        return story_text

    for item in story_text:
        override = overrides.get(str(item["image_order"]))
        if override is not None:
            item["text"] = override

    return story_text


def rebuild_story_context(benchmark_story_text, upstream_story_text, image_paths, context_format):
    benchmark_lookup = {item["image_path"]: item for item in benchmark_story_text}
    upstream_lookup = {item["image_path"]: item for item in upstream_story_text}
    ordered_paths = sorted(
        image_paths,
        key=lambda image_path: benchmark_lookup[image_path]["image_order"],
    )

    text_sources = context_format.get("text_sources", [])
    ordered_texts = []
    for index, image_path in enumerate(ordered_paths):
        source_name = (
            text_sources[index] if index < len(text_sources) else "benchmark"
        )
        source_lookup = benchmark_lookup if source_name == "benchmark" else upstream_lookup
        ordered_texts.append(source_lookup[image_path]["text"])

    if not ordered_texts:
        return ""

    prefix = context_format.get("prefix", "")
    separators = context_format.get("separators", [])
    suffix = context_format.get("suffix", "")

    rebuilt = prefix + ordered_texts[0]
    for separator, text in zip(separators, ordered_texts[1:]):
        rebuilt += separator + text

    if len(ordered_texts) > 1 and len(separators) < len(ordered_texts) - 1:
        for text in ordered_texts[len(separators) + 1 :]:
            rebuilt += " " + text

    rebuilt += suffix
    return rebuilt


def restore_ssid_content(input_json, mapping_json, output_json):
    with input_json.open("r", encoding="utf-8") as handle:
        benchmark = json.load(handle)
    with mapping_json.open("r", encoding="utf-8") as handle:
        mapping = json.load(handle)

    upstream_stories = load_upstream_ssid()
    restored = 0

    for story in benchmark:
        if story.get("dataset") != "ssid":
            continue

        global_id = str(story["global_id"])
        if global_id not in mapping:
            raise KeyError(f"Missing SSID mapping for global_id={global_id}")

        source_story_id = str(mapping[global_id]["source_story_id"])
        if source_story_id not in upstream_stories:
            raise KeyError(
                f"Mapped SSID story_id={source_story_id} not found in upstream SSID files"
            )

        upstream_story_text = rebuild_story_text(upstream_stories[source_story_id])
        story["story_text"] = apply_text_overrides(
            [dict(item) for item in upstream_story_text],
            mapping[global_id].get("text_overrides", {}),
        )

        context_formats = mapping[global_id].get("question_context_format", {})
        for question_id, question in story.get("questions", {}).items():
            question["story_context"] = rebuild_story_context(
                story["story_text"],
                upstream_story_text,
                question.get("image_paths", []),
                context_formats.get(question_id, {}),
            )

        restored += 1

    output_json.write_text(
        json.dumps(benchmark, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Restored SSID stories: {restored}")
    print(f"Saved output: {output_json}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Restore SSID story_text into the benchmark JSON from official SSID downloads."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_JSON,
        help="Benchmark JSON to update. Default: data/multivationbench.json",
    )
    parser.add_argument(
        "--mapping",
        type=Path,
        default=DEFAULT_MAPPING_JSON,
        help="SSID mapping JSON. Default: data/mappings/ssid_mapping.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_JSON,
        help="Output JSON path.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    restore_ssid_content(args.input, args.mapping, args.output)
