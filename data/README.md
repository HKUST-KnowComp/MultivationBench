# MulTivationBench Data

This directory contains the release-safe MulTivationBench benchmark file and
source-mapping metadata used by the recovery scripts.

## Files

| File | Description |
| --- | --- |
| `multivationbench.json` | Release-safe benchmark JSON with question-answer annotations |
| `moviebench_split.json` | MovieBench split metadata used by `scripts/download_moviebench.sh` |
| `mappings/ssid_mapping.json` | Mapping from benchmark story IDs to upstream SSID story IDs |
| `mappings/storyreasoning_mapping.json` | Mapping from benchmark story IDs to upstream StoryReasoning story IDs and frames |

`multivationbench.json` removes SSID and StoryReasoning `story_text` and
question-level `story_context` fields while preserving the MulTivationBench
question-answer annotations. MovieBench story text, question context, and image
paths are kept as packaged.

## Restore SSID Story Content

Download `SSID_Annotations` and `SSID_Images` from the official SSID source, then
place them under:

```text
Datasets/
  SSID/
    SSID_Train.json
    SSID_Test.json
    SSID_Validation.json
    SSID_Images/
      *.jpg
```

Run from the repository root:

```bash
python scripts/restore_ssid_content.py \
  --input data/multivationbench.json \
  --mapping data/mappings/ssid_mapping.json \
  --output data/multivationbench.ssid_restored.json
```

## Restore StoryReasoning Story Content

The StoryReasoning restoration script uses the upstream StoryReasoning loader
when available. If unavailable, it falls back to a local cache at
`result/final_dataset/stories.json` when that file exists.

```bash
python scripts/restore_storyreasoning_content.py \
  --input data/multivationbench.json \
  --mapping data/mappings/storyreasoning_mapping.json \
  --output data/multivationbench.storyreasoning_restored.json
```

## Generate A Combined Restored File

After placing the required upstream data locally, run:

```bash
python scripts/generate_gt_with_story.py \
  --input data/multivationbench.json \
  --output data/multivationbench_with_story.json
```

## MovieBench Notes

MovieBench source videos must be obtained from the upstream MovieBench/LSMDC
source. Place MovieBench scene metadata at:

```text
Datasets/movie/movies_scenes.json
```

Then configure credentials in `scripts/download_moviebench.sh` and run:

```bash
bash scripts/download_moviebench.sh
```

The benchmark image paths encode timestamps, which can be used to extract the
corresponding frames from the downloaded clips.

## License Notes

MulTivationBench derives from MovieBench, StoryReasoning, and SSID. This
directory does not grant redistribution rights for upstream images, videos,
story texts, or substantial upstream source materials. Users must obtain
upstream data directly from the original sources and comply with their licenses.
