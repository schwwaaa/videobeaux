# Captburn Pop-On Examples (testfile.mp4 / testfile.json)

Below are **15 demonstration commands** using the `popon` style for *captburn*, showcasing variations in alignment, styling, color, font, and motion.

---

### 1. Default pop-on (simple white text, bottom-center)
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style popon
```

### 2. Larger type, bold Helvetica, yellow with black outline
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style popon \
  --font "Helvetica Bold" --font-size 56 \
  --primary "#FFD900" --outline "#000000" --outline-width 4
```

### 3. Lower-third placement with left alignment
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style popon \
  --align 1 --margin-v 120
```

### 4. Vintage VHS caption box (opaque background)
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style popon \
  --font "Courier New" --font-size 44 \
  --border-style 3 --back "#000000" --back-opacity 0.85 \
  --primary "#00FF00"
```

### 5. Pop-on at top-center (news style)
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style popon \
  --align 8 --margin-v 80
```

### 6. Pop-on with italic serif font and subtle shadow
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style popon \
  --font "Times New Roman Italic" --italic \
  --shadow 2 --outline "#202020" --outline-width 2
```

### 7. Two-tone color scheme, white text with red outline
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style popon \
  --primary "#FFFFFF" --outline "#FF0000" --outline-width 3
```

### 8. Small upper-left “annotation” captions
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style popon \
  --align 7 --font-size 28 --margin-l 80 --margin-v 40
```

### 9. Motion caption drifting upward
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style popon \
  --move 640,720,640,400,0,2000
```

### 10. Pixelated / retro computer terminal style
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style popon \
  --font "VT323" --font-size 36 --primary "#00FF00" \
  --back "#000000" --back-opacity 0.9 --border-style 3
```

### 11. Narrow text box with wide character spacing
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style popon \
  --spacing 4 --scale-x 85 --scale-y 100
```

### 12. High-contrast subtitle (white on semi-black box)
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style popon \
  --border-style 3 --back "#000000" --back-opacity 0.5 \
  --primary "#FFFFFF" --outline "#000000"
```

### 13. Artistic pastel caption with custom XY position
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style popon \
  --primary "#F9C5D1" --outline "#674F75" --outline-width 2 \
  --x 480 --y 200
```

### 14. Pop-on positioned mid-screen (karaoke-bar look)
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style popon \
  --align 5 --font "Futura Bold" --font-size 48 \
  --back "#0000FF" --back-opacity 0.3
```

### 15. Film-credit look (fade-in, top-right corner)
```bash
python captburn.py -i testfile.mp4 -t testfile.json --style popon \
  --align 9 --font "Baskerville" --italic --shadow 3 \
  --primary "#FFFFFF" --outline "#202020" --outline-width 1 \
  --margin-r 80 --margin-v 100
```

---

✅ These examples show how flexible `captburn` is for stylistic experimentation.  
Would you like equivalent **15 examples for `--style painton`** (word-reveal) next?
