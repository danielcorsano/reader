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
poetry run reader convert --voice "Samantha" --speed 1.0

# Result: audio/short-story.wav
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
poetry run reader config --voice "Daniel"
poetry run reader convert

# Results:
# - audio/sci-fi.wav
# - audio/mystery.wav  
# - audio/romance.wav
```

## Example 3: Configuration Workflow

```bash
# Find your preferred voice
poetry run reader voices | head -20

# Test different voices with a sample
echo "Hello, this is a test of the emergency broadcast system." > text/voice-test.txt

poetry run reader convert --voice "Samantha" --file text/voice-test.txt
poetry run reader convert --voice "Daniel" --file text/voice-test.txt
poetry run reader convert --voice "Alex" --file text/voice-test.txt

# Set your favorite as default
poetry run reader config --voice "Samantha" --speed 1.1

# Confirm settings
poetry run reader config
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
poetry run reader convert --voice "Alex" --speed 0.9

# Result: audio/technical-manual.wav
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
poetry run reader convert --voice "Daniel" --speed 1.0

# Result: audio/tutorial.wav (with automatic chapter detection)
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
poetry run reader config --voice "Samantha"
poetry run reader convert --file text/fiction/fantasy.txt
poetry run reader convert --file text/fiction/sci-fi.txt

# Process tutorials with clear, slower voice
poetry run reader config --voice "Alex" --speed 0.9
poetry run reader convert --file text/tutorials/coding.txt

# Process non-fiction with authoritative voice
poetry run reader config --voice "Daniel" --speed 1.0
poetry run reader convert --file text/non-fiction/history.txt

# Check results
ls -la audio/
```

## Example 7: Speed Optimization for Different Content

```bash
# Create different types of content
echo "Breaking news: Scientists discover new planet..." > text/news.txt
echo "Meditation guide: Close your eyes and breathe deeply..." > text/meditation.txt
echo "Quick recipe: Boil water, add pasta, cook 8 minutes..." > text/recipe.txt

# News - faster pace
poetry run reader convert --voice "Daniel" --speed 1.3 --file text/news.txt

# Meditation - slow, calming pace  
poetry run reader convert --voice "Samantha" --speed 0.7 --file text/meditation.txt

# Recipe - normal, clear pace
poetry run reader convert --voice "Alex" --speed 1.0 --file text/recipe.txt
```

## Example 8: Testing Voice Characteristics

```bash
# Create a test script to try different voices
cat > test-voices.sh << 'EOF'
#!/bin/bash

# Test text
echo "This is a test of different voices. How does this voice sound for audiobook narration?" > text/voice-sample.txt

# Test different voices
voices=("Samantha" "Daniel" "Alex" "Alice" "Thomas")

for voice in "${voices[@]}"; do
    echo "Testing voice: $voice"
    poetry run reader convert --voice "$voice" --file text/voice-sample.txt
    mv audio/voice-sample.wav "audio/test-${voice}.wav"
done

echo "Voice tests complete! Listen to audio/test-*.wav files"
EOF

chmod +x test-voices.sh
./test-voices.sh
```

## Example 9: System Information and Debugging

```bash
# Check system status
poetry run reader info

# List all available voices with details
poetry run reader voices > available-voices.txt
echo "Saved voice list to available-voices.txt"

# Check current configuration
poetry run reader config > current-config.txt
echo "Saved configuration to current-config.txt"

# Test file detection
echo "Test file" > text/test.txt
echo "Test epub" > text/test.epub  
echo "Test pdf content" > text/test.pdf

poetry run reader info  # Should show 3 supported files
```

## Example 10: Advanced Configuration

```bash
# Save current config
poetry run reader config > backup-config.txt

# Test different configurations
poetry run reader config --voice "Samantha" --speed 1.2
poetry run reader convert --file text/sample.txt
mv audio/sample.wav audio/sample-samantha-1.2.wav

poetry run reader config --voice "Daniel" --speed 1.0  
poetry run reader convert --file text/sample.txt
mv audio/sample.wav audio/sample-daniel-1.0.wav

poetry run reader config --voice "Alex" --speed 0.8
poetry run reader convert --file text/sample.txt
mv audio/sample.wav audio/sample-alex-0.8.wav

# Compare results and choose your favorite
echo "Listen to audio/sample-*.wav to compare voices and speeds"

# Restore preferred config (example)
poetry run reader config --voice "Samantha" --speed 1.1
```

## Tips for Best Results

1. **Voice Selection**: Try 3-4 different voices with the same text to find your preference
2. **Speed Tuning**: Start with 1.0, then adjust ±0.1 until comfortable
3. **Content-Specific Settings**: Use slower speeds for technical content, faster for news
4. **File Organization**: Keep source files organized by genre/type for batch processing
5. **Testing**: Always test with a short sample before processing long books

## Coming in Phase 2

- 48 neural voices across 8 languages
- Emotion detection and automatic prosody adjustment
- Character voice mapping for dialogue
- Voice blending and custom voice creation
- MP3/M4A/M4B output with metadata and chapters

## Coming in Phase 3

- Professional audiobook production features
- Dialogue detection and character assignment
- Scene-based narration adjustments
- Batch processing with queue management
- Voice preview and A/B testing interface