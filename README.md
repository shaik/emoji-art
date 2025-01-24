# Emoji Art

A Flask-based web application for creating and manipulating emoji art.

## Features

- Create and customize emoji art
- Web-based interface
- Easy to use and extend

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd emojiArt
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy the environment file and configure it:
```bash
cp .env.example .env
# Edit .env with your settings
```

5. Run the application:
```bash
python app.py
```

The application will be available at http://127.0.0.1:5000

## Emoji Data Format

The application uses a CSV file to store emoji data. Place your `emoji_data.csv` file in the `data/` directory with the following format:

```csv
emoji,color,name
😀,#FFFF00,Smiling Face
🐶,#B5651D,Dog
❤️,#FF0000,Heart
```

### CSV Requirements:
- Headers must be exactly: `emoji,color,name`
- Emoji column: Must contain a single Unicode emoji character
- Color column: Must be a valid hex color code (e.g., #FFFF00)
- Name column: Must be a non-empty string

The CSV file is loaded when the application starts, and the data is stored in memory for fast access.

## Development

### Running Tests
```bash
python -m pytest -v
```

### Project Structure
```
emojiArt/
├── static/          # Static files (JS, CSS)
├── templates/       # HTML templates
├── config/         # Configuration files
├── tests/          # Test files
└── app.py          # Main application file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
