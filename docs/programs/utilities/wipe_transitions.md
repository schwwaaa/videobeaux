---
layout: default
title: wipe_transitions
nav_order: 2
---

# wipe_transitions

## Description

Joins two videos with a wipe transition at the join. The first video plays to its end, the wipe runs over the end of the first video and the start of the second, and the audio crossfades at the same moment.

## Arguments

- `input` (the first video, from the global `-i`)
- `input2` (the second video)
- `preset` (the wipe style, for example `wipeleft` or `fade`)
- `duration` (the length of the wipe, in seconds)

## Program Template

```bash
videobeaux -P wipe_transitions -i first.mp4 -o output.mp4 --input2 second.mp4 --preset VALUE --duration VALUE
```

## Real World Example

```bash
videobeaux -P wipe_transitions -i intro.mp4 -o intro_to_main.mp4 --input2 main.mp4 --preset wipeleft --duration 1.5
```

## Technical Notes

- There is no offset to set. The wipe always starts `duration` seconds before the first video ends, so both clips play in full.
- The output is about `dur1 + dur2 - duration` long.
- Both videos must be at least `duration` seconds long. The program stops with a message if one is shorter.
- The second video is scaled and padded to the first video's size and frame rate.
