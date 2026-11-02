# key_composite

## Description
The second half of Remove Background, as its own program. It puts the subject of the source over a new background (a colour, an image or another video, or transparent), using a matte video you connect. Change the background or the edge clean-up without matting the footage again.

## Purpose
Matting is the slow part. Once you have a good matte, Key Composite lets you try many backgrounds in seconds.

## How It Works
1. **The matte**
   The matte is a grayscale video: white is the subject, black is what goes. Connect a Remove Background node with **View = matte** to the matte input. Any other grayscale video works too.
2. **The composite**
   The source is combined with the matte as its alpha channel, then placed over the background you choose (`background`).
3. **Views**
   `view` = `composite` is the result; `matte` shows the mask; `checkerboard` shows the subject over a checkerboard, useful for checking edges.
4. **Transparency**
   `background = transparent` saves a WebM or MOV with a real alpha channel, as Remove Background does.

## Program Template
```bash
videobeaux -P key_composite -i source.mp4 -o output.mp4 --matte matte.mp4 --background color --bg_color "#00FF00"
```

## Arguments
- **matte**: the grayscale matte video (connect it on the canvas).
- **background**: `auto`, `color`, `image`, `video`, or `transparent`.
- **bg_color**, **bg_image**, **bg_video**: the background to use.
- **view**: `composite`, `matte`, or `checkerboard`.
- **audio**: which sound to keep (the source by default).
- **shrink**, **feather**: edge clean-up. Both default to `0` here, since the matte was cleaned up already.
- **crf**: quality of the encode.

## Real World Example
Matte once with Remove Background (View = matte), then:
1. Connect that matte to a Key Composite node, with the original clip as the source.
2. Set **background = video** and connect a city timelapse as the background.

## Technical Notes
- The matte is scaled to the source's size, so it can be a different resolution.
- A matte made with the static-camera engine is only as good as the empty-scene plate, so check it with View = matte first.
