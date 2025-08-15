# GitHub Crawler

A powerful Python tool for crawling GitHub search results and extracting repository information. This crawler can search for repositories, issues, and wikis based on keywords and extract detailed information including language statistics.

## Features

- 🔍 **Search GitHub** for repositories, issues, and wikis using keywords
- 🌐 **Proxy Support** for anonymous crawling
- 📊 **Language Statistics** extraction for repositories
- 🎯 **Flexible Search Types** - Repositories, Issues, Wikis
- 📈 **Extra Enrichment** - Get owner info and language stats
- 🚀 **Fast & Efficient** - HTML parsing with BeautifulSoup
- 📋 **JSON Output** - Structured data for easy processing

## Installation

### Prerequisites

- Python 3.8 or higher
- pip

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd crawler
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package in development mode:
```bash
pip install -e .
```

## Usage

### Basic Command Structure

```bash
python -m ghcrawler.cli --keywords <keywords> --type <type> [options]
```

### Command Line Arguments

- `--keywords`: Search keywords (required, multiple keywords supported)
- `--type`: Search type - `Repositories`, `Issues`, or `Wikis` (required)
- `--proxies`: Proxy servers in format `host:port` or `scheme://host:port` (optional)
- `--timeout`: Request timeout in seconds (default: 20)
- `--extra`: Include additional information (owner + language stats for repositories)

### Examples

#### 1. Search for Repositories

Basic repository search:
```bash
python -m ghcrawler.cli \
  --keywords openstack nova css \
  --type Repositories
```

With proxy and extra information:
```bash
python -m ghcrawler.cli \
  --keywords openstack nova css \
  --proxies 57.129.81.201:8080 \
  --type Repositories \
  --extra
```

#### 2. Search for Issues

```bash
python -m ghcrawler.cli \
  --keywords bug fix documentation \
  --type Issues
```

#### 3. Search for Wikis

```bash
python -m ghcrawler.cli \
  --keywords api documentation setup \
  --type Wikis
```

#### 4. Using Multiple Proxies

```bash
python -m ghcrawler.cli \
  --keywords python django \
  --proxies 57.129.81.201:8080 192.168.1.100:3128 \
  --type Repositories
```

## Output Format

The tool outputs JSON data with the following structure:

### Basic Output (without --extra)
```json
[
  {
    "url": "https://github.com/owner/repo-name"
  },
  {
    "url": "https://github.com/another-owner/another-repo"
  }
]
```

### Enhanced Output (with --extra for repositories)
```json
[
  {
    "url": "https://github.com/owner/repo-name",
    "extra": {
      "owner": "owner",
      "language_stats": {
        "Python": 65.2,
        "JavaScript": 20.1,
        "CSS": 14.7
      }
    }
  }
]
```

## Supported Search Types

1. **Repositories** - Search for GitHub repositories
2. **Issues** - Search for GitHub issues and pull requests
3. **Wikis** - Search for GitHub wiki pages

## Configuration

The crawler uses the following default settings:
- **User Agent**: Modern Chrome browser string
- **Timeout**: 20 seconds per request
- **Request Headers**: Standard browser headers

## Development

### Code Quality

```bash
# Sort imports with isort
isort ghcrawler/ tests/

# Check import sorting without making changes
isort --check-only ghcrawler/ tests/

# Sort imports in a specific file
isort ghcrawler/cli.py
```

### Running Tests

```bash
# Run all tests
pytest -v

# Run tests with coverage report
pytest --cov=ghcrawler --cov-report=term-missing

# Run tests with HTML coverage report
pytest --cov=ghcrawler --cov-report=html

# Run tests with both terminal and HTML coverage reports
pytest --cov=ghcrawler --cov-report=html --cov-report=term-missing

# Open HTML coverage report in browser
open htmlcov/index.html
```

### Code Coverage

The project maintains **99% code coverage** with comprehensive test suites covering:

- **CLI functionality** - Command line argument parsing and execution
- **Crawler logic** - GitHub search and data extraction
- **HTML parsing** - URL extraction and language statistics parsing
- **Error handling** - Invalid inputs and network errors
- **Edge cases** - Empty results, malformed data, etc.

**Test Quality Features:**
- **DRY Principle** - Reusable test fixtures and helper functions
- **Deep Validation** - Exact URL matching and comprehensive result validation
- **Edge Case Coverage** - Negative percentages, zero values, invalid inputs
- **Multiple Search Types** - Repositories, Issues, and Wikis testing

**Current Coverage Status:**
- `ghcrawler/__init__.py`: 100%
- `ghcrawler/cli.py`: 94%
- `ghcrawler/crawler.py`: 96%
- `ghcrawler/parsers.py`: 99%
- `ghcrawler/selectors.py`: 100%
- **Overall**: 97%

**Test Statistics:**
- **26 test cases** covering all major functionality
- **7 CLI tests** - Different argument combinations and search types
- **6 Crawler tests** - Configuration, error handling, and data processing
- **12 Parser tests** - URL extraction and language statistics parsing
- **1 Error handling test** - Network and HTTP error scenarios

### Project Structure

```
ghcrawler/
├── __init__.py      # Package initialization
├── cli.py          # Command-line interface
├── crawler.py      # Main crawler logic
├── parsers.py      # HTML parsing functions
└── selectors.py    # CSS selectors and constants

tests/
├── test_cli.py     # CLI tests
├── test_crawler.py # Crawler tests
└── test_errors.py  # Error handling tests
```

## Dependencies

### Production Dependencies
- **requests**: HTTP library for making requests
- **beautifulsoup4**: HTML parsing and extraction

### Development Dependencies
- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **isort**: Import sorting and organization

## Error Handling

The crawler includes robust error handling for:
- Network timeouts
- HTTP errors
- Invalid search types
- Missing keywords
- Proxy connection issues

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational and research purposes. Please respect GitHub's terms of service and rate limits when using this crawler. Consider using GitHub's official API for production applications. 
