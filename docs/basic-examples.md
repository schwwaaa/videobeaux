
# Example #1

## Usage
``` bash
videobeaux --program PROGRAM --input INPUT_FILE --output OUTPUT_FILE
```

## Practical
``` bash
videobeaux \
--program bad_predator \
--input example.mp4 \
--output example_bp.mp4
```

## Output
<video controls width="50%">
    <source src="https://github.com/user-attachments/assets/fe45aa80-9878-4d15-bc64-87dd25071855" type="video/mp4">
</video>

# Example #2

## Usage
``` bash
videobeaux --program PROGRAM --input INPUT_FILE --output OUTPUT_FILE --args ARGUMENTS
```

## Practical
``` bash
videobeaux \
--program stutter_pro \
-i example.mp4 \
-o stutter_example.mp4 \
--stutter 2
```

## Output
<video controls width="50%">
    <source src="https://github.com/user-attachments/assets/fec22179-8e40-49e5-b591-c9d5fb07e31b" type="video/mp4">
</video>

# Example #3

## Usage
``` bash
videobeaux --program PROGRAM --input INPUT_FILE --output OUTPUT_FILE --chain CHAIN
```

## Practical
``` bash
videobeaux \
--program chain_builder \
--input example.mp4 \
--output chainedoutput.mp4 \
--chain rb_blur,soapblind,lsd_feedback \
--force
```

## Output
<video controls width="50%">
    <source src="https://github.com/user-attachments/assets/ac321c77-4757-4846-b838-6847472e7e09" type="video/mp4">
</video>