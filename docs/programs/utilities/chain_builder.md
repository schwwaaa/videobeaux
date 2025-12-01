# chain_builder

## Description

Assembles a sequence of videobeaux program steps into a single automated workflow, chaining multiple transformations into one output

## Arguments

- `chain`

## Program Template

```bash
videobeaux -P chain_builder -i input.mp4 -o output.mp4 --chain VALUE
```

## Real World Example

```bash
videobeaux -P chain_builder -i myvideo.mp4 -o chain_builder_styled.mp4 --chain EXAMPLE
```
