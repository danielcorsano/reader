# Reader Examples

## Example 1: Convert a Simple Text File

```bash
# Create a simple story
cat > text/short-story.txt << 'EOF'
Chapter 1: The Beginning

Once upon a time, in a small village, there lived a young programmer who discovered the magic of text-to-speech technology.

Chapter 2: The Discovery

The programmer realized they could turn any written story into an audiobook with just a few commands.

Chapter 3: The Adventure Begins

And so began their journey into the world of automated audiobook creation.
EOF

# Convert to audiobook
reader convert --voice "Samantha" --speed 1.0

# Result: finished/short-story_kokoro_am_michael.mp3
```

## Example 2: Process Multiple Books

```bash
# Add several books
echo "# Science Fiction Story
This is a futuristic tale..." > text/sci-fi.md

echo "# Mystery Novel  
The detective arrived at midnight..." > text/mystery.md

echo "# Romance Story
Under the moonlight..." > text/romance.md

# Convert all with different voices
reader config --voice "Daniel"
reader convert

# Results:
# - finished/sci-fi_kokoro_am_michael.mp3
# - finished/mystery_kokoro_am_michael.mp3
# - finished/romance_kokoro_am_michael.mp3
```

## Example 3: Configuration Workflow

```bash
# Find your preferred voice
reader voices | head -20

# Test different Kokoro voices with a sample
echo "Hello, this is a test of the emergency broadcast system." > text/voice-test.txt

reader convert --voice af_sarah --file text/voice-test.txt
reader convert --voice am_michael --file text/voice-test.txt
reader convert --voice bf_emma --file text/voice-test.txt

# Set your favorite as default
reader config --voice am_michael --speed 1.0

# Confirm settings
reader config
```

## Example 4: PDF Document Processing

```bash
# Simulate a PDF (create a text version)
cat > text/technical-manual.txt << 'EOF'
Technical Manual: Widget Assembly

Page 1: Introduction
This manual covers the assembly of Widget Model XR-1000.

Page 2: Components
The following components are included in your kit:
- Widget base (1x)
- Widget screws (4x)
- Widget manual (1x)

Page 3: Assembly
Step 1: Place the widget base on a flat surface.
Step 2: Insert screws into designated holes.
Step 3: Tighten until secure.

Page 4: Conclusion
Your widget is now assembled and ready for use.
EOF

# Convert with slower, clear speech for technical content
reader convert --voice am_michael --speed 0.9

# Result: finished/technical-manual_kokoro_am_michael_speed0p9.mp3
```

## Example 5: Markdown with Chapters

```bash
# Create a structured markdown document
cat > text/tutorial.md << 'EOF'
# Python Tutorial

## Chapter 1: Getting Started

Python is a powerful programming language that's easy to learn.

## Chapter 2: Variables

In Python, you can create variables like this:
```python
name = "Alice"
age = 25
```

## Chapter 3: Functions

Functions help organize your code:
```python
def greet(name):
    return f"Hello, {name}!"
```

## Chapter 4: Conclusion

You've learned the basics of Python programming!
EOF

# Convert with clear, educational voice
reader convert --voice am_michael --speed 1.0

# Result: finished/tutorial_kokoro_am_michael.mp3 (with automatic chapter detection)
```

## Example 6: Batch Processing Workflow

```bash
# Organize books by genre
mkdir -p text/fiction text/non-fiction text/tutorials

# Add books to categories
echo "Fantasy epic adventure..." > text/fiction/fantasy.txt
echo "Space exploration thriller..." > text/fiction/sci-fi.txt
echo "How to learn programming..." > text/tutorials/coding.txt
echo "History of ancient Rome..." > text/non-fiction/history.txt

# Process all fiction with one voice
reader config --voice af_sarah
reader convert --file text/fiction/fantasy.txt
reader convert --file text/fiction/sci-fi.txt

# Process tutorials with clear, slower voice
reader config --voice am_michael --speed 0.9
reader convert --file text/tutorials/coding.txt

# Process non-fiction with British narrator
reader config --voice bm_george --speed 1.0
reader convert --file text/non-fiction/history.txt

# Check results
ls -la finished/
```

## Example 7: Speed Optimization for Different Content

```bash
# Create different types of content
echo "Breaking news: Scientists discover new planet..." > text/news.txt
echo "Meditation guide: Close your eyes and breathe deeply..." > text/meditation.txt
echo "Quick recipe: Boil water, add pasta, cook 8 minutes..." > text/recipe.txt

# News - faster pace
reader convert --voice am_michael --speed 1.3 --file text/news.txt

# Meditation - slow, calming pace
reader convert --voice af_sarah --speed 0.7 --file text/meditation.txt

# Recipe - normal, clear pace
reader convert --voice bf_emma --speed 1.0 --file text/recipe.txt
```

## Example 8: Testing Voice Characteristics

```bash
# Create a test script to try different voices
cat > test-voices.sh << 'EOF'
#!/bin/bash

# Test text
echo "This is a test of different voices. How does this voice sound for audiobook narration?" > text/voice-sample.txt

# Test different Kokoro voices
voices=("af_sarah" "am_michael" "bf_emma" "bm_george" "af_nicole")

for voice in "${voices[@]}"; do
    echo "Testing voice: $voice"
    reader convert --voice "$voice" --file text/voice-sample.txt
    # Files automatically saved with voice name in filename
done

echo "Voice tests complete! Listen to finished/voice-sample_*.mp3 files"
EOF

chmod +x test-voices.sh
./test-voices.sh
```

## Example 9: System Information and Debugging

```bash
# Check system status
reader info

# List all available voices with details
reader voices > available-voices.txt
echo "Saved voice list to available-voices.txt"

# Check current configuration
reader config > current-config.txt
echo "Saved configuration to current-config.txt"

# Test file detection
echo "Test file" > text/test.txt
echo "Test epub" > text/test.epub  
echo "Test pdf content" > text/test.pdf

reader info  # Should show 3 supported files
```

## Example 10: Advanced Configuration

```bash
# Test different configurations
reader convert --voice af_sarah --speed 1.2 --file text/sample.txt
reader convert --voice am_michael --speed 1.0 --file text/sample.txt
reader convert --voice bf_emma --speed 0.8 --file text/sample.txt

# Compare results - files are named with voice and speed
echo "Listen to finished/sample_*.mp3 to compare voices and speeds"

# Set preferred config
reader config --voice am_michael --speed 1.0
```

## Example 11: Strip Unwanted Chapters Before Converting

```bash
# Strip a textbook to remove front/back matter
reader strip textbook.epub

# Example output (EPUB uses structural markup from h1-h6 tags):
#   0: Cover Page
#      "Published by Academic Press..."
#   1: Table of Contents
#      "Chapter 1...page 1, Chapter 2...page 45..."
#   2: Foreword
#      "It is my great pleasure to introduce..."
#   3: Chapter 1 - Introduction
#      "This textbook explores the fundamentals of..."
#   ...
#   15: Bibliography
#      "Anderson, J. (2019). Research Methods..."
#   16: Index
#      "A: Abstract algebra, 12; Algorithms, 45..."

# Auto-strip non-content? [y/n]: y
# Sensitivity: 0.5 | Stripped 2 from front, 2 from back
# Keeping chapters 2-14 (13 of 17)
# Show ending? (may contain spoilers) [y/n]: n
# [3] Accept
# Saved: textbook_stripped.epub
# Convert to audiobook? [y/n]: y
```

## Example 12: Strip PDF with Heading Detection

```bash
# PDFs get tiered chapter detection:
# 1. No marked chapters found (pages only)
# 2. Heading detection finds: Translator's Note, Preface, Part I, Part II, Index
# 3. Auto-strip flags front/back matter
reader strip "Wittgenstein - Philosophical Investigations.pdf"

# Detected 6 sections from text analysis
#   0: Translator's Note
#   1: Preface
#   2: Part I
#   3: Part II
#   4: Index
# Auto-strip suggests removing Translator's Note (front) — conservative on back

# Saves as: Wittgenstein - Philosophical Investigations_stripped.txt
```

## Tips for Best Results

1. **Voice Selection**: Try 3-4 different voices with the same text to find your preference
2. **Speed Tuning**: Start with 1.0, then adjust ±0.1 until comfortable
3. **Content-Specific Settings**: Use slower speeds for technical content, faster for news
4. **File Organization**: Keep source files organized by genre/type for batch processing
5. **Testing**: Always test with a short sample before processing long books

## Advanced Features

✅ **Currently Available:**
- 54 neural Kokoro voices across 9 languages
- Emotion detection and prosody adjustment
- Character voice mapping for dialogue
- MP3/M4A/M4B output with metadata
- 4 progress visualization styles (simple, tqdm, rich, timeseries)
- Checkpoint recovery for interrupted conversions
- Apple Neural Engine optimization
- **Text stripping** with tiered chapter detection, auto-strip classifier, and spoiler-protected preview

📚 **For More Details:**
- See [PHASE3_FEATURES.md](PHASE3_FEATURES.md) for full feature documentation
- See [KOKORO_SETUP.md](KOKORO_SETUP.md) for model setup
- See [USAGE.md](USAGE.md) for complete command reference