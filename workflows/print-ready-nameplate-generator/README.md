<p align="center">
  <img src="branding/logo.png" width="128" alt="Print-ready Nameplate Generator logo">
</p>

# Print-ready Nameplate Generator

Generate editable A4 PowerPoint decks for foldable triangular desk nameplates
from a CSV list. It turns one reusable layout into one-card-per-page and
two-cards-per-page print files while preserving editable text and vector shapes.

中文说明：把带有“姓名”列的 CSV 名单批量生成可编辑的 A4 三角姓名牌 PPTX，
同时提供单个版和两拼版。公开仓库只包含通用程序和虚构示例，不包含真实学生
名单、手写照片或交付文件。

## FlowFoundry AI relationship

This project is cataloged by
[FlowFoundry AI](https://github.com/ryanshi1103/ai-workflow-foundry) as an
independent reference workflow. Its deterministic geometry, input validation,
safe filenames, and real LibreOffice acceptance process are reusable patterns;
the generator remains a focused product with its own release cycle.

## What it solves

- Avoids manually copying dozens of names into a slide template.
- Uses millimetre-based geometry so printing at 100% keeps physical dimensions.
- Rotates the upper face correctly so both sides are upright after folding.
- Keeps names, labels, colors and shapes editable in PowerPoint/LibreOffice.
- Sanitizes output filenames so a display label cannot escape the output folder.

## Input

Create a UTF-8 CSV containing a `姓名` column:

```csv
姓名
林一
陈小满
周星河
```

A fictional example is provided at `examples/names.csv`.

## Run

The generator uses LibreOffice PyUNO. Start a local, headless LibreOffice
listener first:

```bash
soffice --headless --accept='socket,host=localhost,port=2002;urp;' \
  --norestore --nofirststartwizard &
```

Then generate both decks:

```bash
python3 scripts/generate_batch_nameplates.py examples/names.csv output \
  --class-label '示例班级' \
  --organization-label '示例活动' \
  --english-label 'WELCOME'
```

Print at `100%` or `Actual size`; do not use “Fit to page”. The solid border is
the cut line and the dashed lines are folds.

## Tests

Pure input and filename helpers can be tested without LibreOffice:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q scripts tests
```

## Privacy

Names are read locally and written only into the requested output deck. Do not
commit real participant lists or generated decks unless every person has given
appropriate consent.

## License

MIT.
