<p align="center">
  <img src="https://github.com/schwwaaa/videobeaux/blob/main/assets/videobeaux-tv-icon-full.png?raw=true" width="420" alt="Videobeaux television mascot and wordmark">
</p>

<!-- <h1 align="center">Videobeaux</h1> -->

<!-- <p align="center"><strong>Break, bend, repair, and automate video.</strong></p> -->

<p align="center">A friendly command-line video toolkit for artists, archivists, researchers, editors, educators, and creative technologists.</p>

<p align="center">
  <a href="https://videobeaux.online">Website</a> ·
  <a href="https://videobeaux.online/docs.html">Documentation</a> ·
  <a href="https://github.com/schwwaaa/videobeaux">Repository</a> ·
  <a href="https://ko-fi.com/F1F71V9CQG">Support</a>
</p>

---

## What is Videobeaux?

Videobeaux is a collection of focused video-processing programs that share one consistent command-line interface.

It combines deliberately destructive effects with practical media utilities, making it useful for both experimentation and production. You can datamosh footage, repeat or reorder frames, composite multiple sources, extract images or audio, build contact sheets, burn captions, convert formats, repair media, and chain multiple programs into repeatable workflows.

Videobeaux is not a traditional nonlinear editor. It is a workshop of small tools that can be used independently or connected together.

> Built for artists by artists. Feed it a video, choose a program, and let the television do something useful—or wonderfully incorrect.

## Core workflow

```text
Input → Program → Output → Chain it again
```

```bash
videobeaux \
  --program PROGRAM \
  --input INPUT_FILE \
  --output OUTPUT_FILE \
  [program options]
```

Processed outputs can then be passed into another program or assembled into a multi-stage chain.

## What can it do?

### Create and distort

- Controlled datamoshing
- Frame stutter and repetition
- Feedback and delay
- Smear, split, scroll, loop, and repaint effects
- Deliberate compression damage
- Experimental frame-order manipulation

### Repair and convert

- Container conversion
- Dimension normalization
- Gamma correction
- Frame interpolation
- LUT application
- HDR-to-SDR tonemapping
- Delivery-oriented media preparation

### Inspect and extract

- Frame extraction
- Audio extraction
- Thumbnail generation
- Contact sheets
- Metadata inspection
- Media fingerprinting
- Asset isolation

### Compose and automate

- JSON-driven multilayer compositing
- Caption and subtitle burning
- Repeatable command-line processing
- Program chains
- Batch-oriented workflows
- Scriptable media pipelines

## Featured programs

| Program | Type | Purpose |
|---|---|---|
| `crossmosh` | Effect | Controlled datamoshing with motion-vector, GOP, decay, frame-order, and source-blending controls |
| `lagkage` | Effect | JSON-driven multilayer video composition without a traditional timeline |
| `stutter_pro` | Effect | Rhythmic frame holds, skips, and timeline interruptions |
| `bad_predator` | Effect | Deliberately broken heat-vision processing and a simple introduction to the standard workflow |
| `chain_builder` | Utility | Passes the output of one compatible program directly into the next |
| `captburn` | Utility | Burns captions or subtitles into video |
| `thumbs` | Utility | Generates thumbnails, labeled stills, and tiled contact sheets |
| `extract_frames` | Utility | Exports sequential image frames from a video |
| `tonemap_hdr_sdr` | Utility | Converts HDR footage to SDR with selectable tonemapping and output controls |

The complete program reference is available in the [documentation](https://schwwaaa.github.io/videobeaux/docs.html).

## Quick start

### 1. Install

On macOS or Linux:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/schwwaaa/videobeaux/refs/heads/main/install.sh)"
```

Windows users should follow the platform-specific instructions in the [documentation](https://schwwaaa.github.io/videobeaux/docs.html#installation).

### 2. Inspect the available programs

```bash
videobeaux --help
```

### 3. Process a video

```bash
videobeaux \
  --program bad_predator \
  --input example.mp4 \
  --output example_bp.mp4
```

### 4. Use program-specific controls

```bash
videobeaux \
  --program stutter_pro \
  --input example.mp4 \
  --output stutter_example.mp4 \
  --stutter 2
```

### 5. Chain multiple programs

```bash
videobeaux \
  --program chain_builder \
  --input example.mp4 \
  --output chained-output.mp4 \
  --chain rb_blur,soapblind,lsd_feedback \
  --force
```

## Documentation

The project documentation is available as a single static page:

**[Open the Videobeaux documentation](https://schwwaaa.github.io/videobeaux/docs.html)**

It includes installation, getting started, examples, the global command structure, effect references, utility references, program-specific arguments, and workflow guidance.

The documentation does not require Jekyll, Ruby, Bundler, or a Gemfile. It is published as a static `docs.html` file.

## Website

**[Visit the Videobeaux website](https://schwwaaa.github.io/videobeaux/)**

The site includes the toolkit overview, featured programs, working examples, installation guidance, process illustrations, and links to the complete documentation.

## Design philosophy

Videobeaux is built around a simple idea:

> Small, focused tools become more powerful when they can be combined.

Each program is intended to be understandable on its own. Together, they form a flexible processing system that can support one-off experiments, repeatable studio workflows, archival work, and automated pipelines.

## Who is it for?

Videobeaux is designed for:

- Video artists
- Experimental filmmakers
- Archivists
- Creative coders
- Researchers
- Educators
- Editors
- Media laboratories
- Batch-processing workflows
- Artists building repeatable processing pipelines

## Accessibility and approachability

The public website and documentation aim to provide plain-language explanations, a consistent command structure, practical examples, readable technical documentation, keyboard-accessible navigation, reduced-motion support, high-contrast interface design, and clear links between the website, docs, and repository.

## Project structure

```text
videobeaux/
├── README.md
├── index.html
├── docs.html
├── install.sh
├── assets/
├── img/
├── programs/
└── examples/
```

For current architecture and program-specific details, use the repository source and published documentation together.

## Contributing

Contributions are welcome when they improve reliability, documentation, portability, accessibility, or usefulness.

Helpful contributions may include bug fixes, platform testing, documentation corrections, improved examples, new focused programs, accessibility improvements, installation fixes, and reproducible issue reports.

Before submitting substantial changes, open an issue describing the problem, intended behavior, and proposed scope.

## Reporting problems

When opening an issue, include:

- Operating system
- Videobeaux command used
- Input format
- Expected behavior
- Actual behavior
- Complete terminal output
- A minimal reproducible example when possible

Do not upload private or copyrighted media unless you have permission to share it.

## Support the project

<p>
  <a href="https://ko-fi.com/F1F71V9CQG">
    <img src="https://ko-fi.com/img/githubbutton_sm.svg" alt="Support Videobeaux on Ko-fi">
  </a>
</p>

## License

See the repository license file for the current licensing terms.

---

<p align="center">
  <strong>Videobeaux</strong><br>
  Built for artists by artists.<br>
  It's your best friend.
</p>
