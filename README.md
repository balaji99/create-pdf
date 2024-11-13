# PDF File Converter

A Python utility for combining and transforming multiple files (PDFs and images) into a single PDF document.

## Features

- Combine multiple PDFs and images into a single PDF file
- Support for various image formats (PNG, JPG, JPEG, TIFF, BMP)
- Page transformation options:
  - Rotate pages (90°, 180°, 270°)
  - Flip pages horizontally or vertically
- Recursive directory processing
- Lexicographical ordering of files
- Configurable via JSON
- Handles existing output files with options to overwrite or auto-rename
- Comprehensive logging system

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install pypdf Pillow
```

## Usage

Run the script using:

```bash
python create-pdf.py config.json output.pdf [--debug]
```

Arguments:
- `config.json`: Path to your configuration file
- `output.pdf`: Desired output PDF path
- `--debug`: Optional flag to enable debug logging

## Configuration File Format

The configuration file should be in JSON format. Here's an example:

```json
{
  "files": [
    "path/to/single/file.pdf",
    {
      "files": ["directory/path"],
      "options": ["rotate90", "recursive"]
    },
    {
      "files": ["path/to/images/*.jpg"],
      "options": ["flipH"]
    }
  ]
}
```

### Available Options

- `rotate90`: Rotate page 90° counter-clockwise
- `rotate180`: Rotate page 180°
- `rotate270`: Rotate page 270° counter-clockwise
- `flipH`: Flip page horizontally
- `flipV`: Flip page vertically
- `recursive`: Process directories recursively

## Features in Detail

### File Handling
- Processes individual files or entire directories
- Maintains lexicographical order of files within each context
- Supports both PDFs and common image formats
- Automatically converts RGBA images to RGB

### Output Management
- Checks for existing output files
- Provides options to:
  1. Overwrite existing file
  2. Use an automatically generated alternative filename
  3. Cancel the operation

### Logging
- Comprehensive logging system with configurable levels
- Debug mode for detailed operation tracking
- Logs include timestamps and severity levels

## Error Handling

The script includes robust error handling for:
- Invalid configuration files
- Missing input files
- Unsupported file types
- File conversion failures
- General processing errors

## Requirements

- Python 3.6+
- pypdf
- Pillow (Python Imaging Library)

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
