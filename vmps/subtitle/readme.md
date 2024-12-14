In an `.ass` subtitle file, the `[V4+ Styles]` section defines the visual styling for subtitles, such as font, color, size, alignment, and more. Here's a detailed explanation of each parameter in the `Format` and `Style` lines.

Check the [docs](http://www.tcax.org/docs/ass-specs.htm), section "5. Style Lines, [v4+ Styles] section" for details

---

### **Format Line**
The `Format` line specifies the parameters used in the `Style` definitions.

Example:
```ass
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
```

---

### **Style Line**
Each `Style` line defines the attributes of a specific style and corresponds to the parameters in the `Format` line.

Example:
```ass
Style: Default,Arial,36,&H00FFFFFF,&H00FF0000,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1
```

#### Parameters Explained:
1. **Name**  
   The name of the style, which can be referenced in the `[Events]` section.  
   - Example: `Default`.

2. **Fontname**  
   The font family for the text.  
   - Example: `Arial`, `Times New Roman`.

3. **Fontsize**  
   The size of the text, in pixels.  
   - Example: `36`.

4. **PrimaryColour**  
   The main color of the text, in `&HBBGGRR` format.  
   - Example: `&H00FFFFFF` (white).

5. **SecondaryColour**  
   Used in karaoke effects to indicate the "progress" color of the text.  
   - Example: `&H00FF0000` (red).

6. **OutlineColour**  
   The color of the text border (outline).  
   - Example: `&H00000000` (black).

7. **BackColour**  
   The color of the shadow behind the text.  
   - Example: `&H80000000` (semi-transparent black).

8. **Bold**  
   Whether the text is bold.  
   - `0`: Normal text.  
   - `-1`: Bold text.  
   - Example: `0` (not bold).

9. **Italic**  
   Whether the text is italicized.  
   - `0`: Normal text.  
   - `-1`: Italicized text.  
   - Example: `0` (not italic).

10. **Underline**  
    Whether the text is underlined.  
    - `0`: No underline.  
    - `-1`: Underlined text.  
    - Example: `0` (no underline).

11. **StrikeOut**  
    Whether the text is struck through.  
    - `0`: No strikethrough.  
    - `-1`: Strikethrough text.  
    - Example: `0` (no strikethrough).

12. **ScaleX**  
    Horizontal scaling of the text, in percentage.  
    - Example: `100` (normal width), `150` (wider text).

13. **ScaleY**  
    Vertical scaling of the text, in percentage.  
    - Example: `100` (normal height), `50` (shorter text).

14. **Spacing**  
    Additional spacing between characters, in pixels.  
    - Example: `0` (default spacing).

15. **Angle**  
    The rotation of the text, in degrees.  
    - `0`: No rotation.  
    - Positive values rotate counter-clockwise.  
    - Example: `0` (default orientation).

16. **BorderStyle**  
    Defines whether the text has an outline or a box.  
    - `1`: Outline and shadow.  
    - `3`: Solid background box.  
    - Example: `1` (outline and shadow).

17. **Outline**  
    Thickness of the text border (outline), in pixels.  
    - Example: `2` (2-pixel outline).

18. **Shadow**  
    Thickness of the shadow, in pixels.  
    - Example: `0` (no shadow), `3` (3-pixel shadow).

19. **Alignment**  
    The alignment of the text within the screen.  
    - `1`: Bottom-left.  
    - `2`: Bottom-center.  
    - `3`: Bottom-right.  
    - `4`: Middle-left.  
    - `5`: Middle-center.  
    - `6`: Middle-right.  
    - `7`: Top-left.  
    - `8`: Top-center.  
    - `9`: Top-right.  
    - Example: `2` (bottom-center).

20. **MarginL**  
    Left margin, in pixels. Overrides the default style's left margin if specified in an event.  
    - Example: `10` (10 pixels from the left edge).

21. **MarginR**  
    Right margin, in pixels. Overrides the default style's right margin if specified in an event.  
    - Example: `10` (10 pixels from the right edge).

22. **MarginV**  
    Vertical margin, in pixels.  
    - For bottom-aligned text, it represents the distance from the bottom of the screen.  
    - Example: `10` (10 pixels from the bottom).

23. **Encoding**  
    Specifies the font encoding to support different languages. Common values:  
    - `0`: ANSI (Western languages).  
    - `1`: Default English.  
    - Other values depend on the language/font.  
    - Example: `1`.

---

### Example Style
```ass
Style: Subtitle,Times New Roman,48,&H00FFFFFF,&H00FF0000,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,20,20,20,1
```

- **Name**: `Subtitle`.  
- **Fontname**: `Times New Roman`.  
- **Fontsize**: `48`.  
- **PrimaryColour**: White.  
- **SecondaryColour**: Red (for karaoke effects).  
- **OutlineColour**: Black.  
- **BackColour**: Semi-transparent black.  
- **Bold**: Yes (`-1`).  
- **Italic**: No (`0`).  
- **Underline**: No (`0`).  
- **ScaleX / ScaleY**: 100% (default).  
- **BorderStyle**: Outline and shadow (`1`).  
- **Outline**: 3-pixel thickness.  
- **Shadow**: 1-pixel shadow.  
- **Alignment**: Bottom-center (`2`).  
- **Margins**: 20 pixels on left, right, and bottom.
