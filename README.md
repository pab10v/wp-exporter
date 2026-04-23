# WP Exporter - WordPress XML to HTML/Markdown Converter

A powerful Python tool that converts WordPress XML export files to HTML or Markdown with advanced filtering, categorization, and content analysis features.

## Features

- ✅ **Multiple Export Formats**: HTML and Markdown output
- ✅ **Advanced Filtering**: Filter by date, author, tags, categories, word count
- ✅ **Content Analysis**: Detailed statistics and reading time estimates
- ✅ **Smart Categorization**: Auto-organize articles by categories
- ✅ **Plugin Cleanup**: Remove WordPress plugin shortcodes
- ✅ **Custom Styling**: Support for custom CSS and branding
- ✅ **Category Discovery**: List all available categories before extraction
- ✅ **SEO Metadata**: Extract dates, authors, tags, and meta descriptions

## Installation

No dependencies required! Uses only Python standard library.

```bash
# Make the script executable
chmod +x wp-exporter.py

# Or run with Python
python3 wp-exporter.py
```

## Quick Start

### Basic Usage

```bash
# Convert XML to HTML (auto-generates output filename)
python3 wp-exporter.py wordpress.xml

# Convert with custom output filename
python3 wp-exporter.py wordpress.xml my-blog.html

# Convert to Markdown
python3 wp-exporter.py wordpress.xml --format markdown
```

### Discover Available Categories

```bash
# List all categories with article counts
python3 wp-exporter.py wordpress.xml --list-categories
```

**Example Output:**
```
============================================================
📂 AVAILABLE CATEGORIES
============================================================
Total unique categories: 11
Total categorized articles: 474

Categories (sorted by article count):
------------------------------------------------------------
 1. Insurance                      (178 articles)
 2. Financial Planning             (94 articles)
 3. Retirement                     (57 articles)
 4. Investment                     (42 articles)
 5. Savings                        (35 articles)
------------------------------------------------------------
```

## Advanced Features

### Content Filtering

```bash
# Filter by date range
python3 wp-exporter.py wordpress.xml --date-range 2023-01-01,2024-12-31

# Filter by specific author
python3 wp-exporter.py wordpress.xml --author "john-doe"

# Filter by tags
python3 wp-exporter.py wordpress.xml --tags "insurance,retirement"

# Filter by categories
python3 wp-exporter.py wordpress.xml --categories "Insurance,Financial"

# Filter by minimum word count
python3 wp-exporter.py wordpress.xml --min-length 500

# Combine multiple filters
python3 wp-exporter.py wordpress.xml \
  --date-range 2023-01-01,2024-12-31 \
  --author "john-doe" \
  --categories "Insurance" \
  --min-length 300
```

### Content Analysis

```bash
# Show detailed statistics
python3 wp-exporter.py wordpress.xml --stats

# Statistics with filtering
python3 wp-exporter.py wordpress.xml --stats --date-range 2023-01-01,2024-12-31
```

**Example Statistics Output:**
```
==================================================
📊 CONTENT STATISTICS
==================================================
📝 Total articles: 213

📈 Word count analysis:
   Total words: 194,524
   Average per article: 913
   Shortest article: 2 words
   Longest article: 7,883 words
   Total reading time: 16.2 hours

📂 Top categories:
   Insurance: 178 articles
   Financial Planning: 94 articles
   Retirement: 57 articles

✍️ Authors:
   john: 88 articles
   jane: 66 articles
   editor: 30 articles
==================================================
```

### Smart Categorization

```bash
# Auto-organize by top 5 categories
python3 wp-exporter.py wordpress.xml --cat 5

# Organize by top 3 categories with statistics
python3 wp-exporter.py wordpress.xml --cat 3 --stats

# Combine with filtering
python3 wp-exporter.py wordpress.xml --cat 5 --date-range 2023-01-01,2024-12-31
```

### Plugin Cleanup

```bash
# Remove WordPress plugin shortcodes (Fusion Builder, etc.)
python3 wp-exporter.py wordpress.xml --clean

# Combine with other features
python3 wp-exporter.py wordpress.xml --clean --cat 5 --stats
```

### Custom Styling

```bash
# Use custom CSS file
python3 wp-exporter.py wordpress.xml --css my-style.css

# Add custom branding
python3 wp-exporter.py wordpress.xml --branding "My Awesome Blog"

# Combine both
python3 wp-exporter.py wordpress.xml --css my-style.css --branding "My Blog"
```

## Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `input.xml` | WordPress XML export file | `wordpress.xml` |
| `output.html` | Output file (optional) | `my-blog.html` |
| `--clean, -c` | Remove plugin shortcodes | `--clean` |
| `--cat <n>` | Organize by n main categories | `--cat 5` |
| `--date-range <start,end>` | Filter by date range | `--date-range 2023-01-01,2024-12-31` |
| `--author <name>` | Filter by author | `--author "john-doe"` |
| `--tags <tag1,tag2>` | Filter by tags | `--tags "insurance,retirement"` |
| `--categories <cat1,cat2>` | Filter by categories | `--categories "Insurance,Financial"` |
| `--min-length <n>` | Minimum word count | `--min-length 500` |
| `--stats` | Show content statistics | `--stats` |
| `--list-categories` | List all available categories | `--list-categories` |
| `--format <format>` | Export format (html/markdown) | `--format markdown` |
| `--template <file>` | Custom HTML template | `--template my-template.html` |
| `--css <file>` | Custom CSS file | `--css my-style.css` |
| `--branding <text>` | Custom branding text | `--branding "My Blog"` |

## Real-World Examples

### Example 1: Blog Migration
```bash
# Extract all insurance articles from 2023, clean plugins, organize by category
python3 wp-exporter.py wordpress.xml \
  --categories "Insurance" \
  --date-range 2023-01-01,2023-12-31 \
  --clean \
  --cat 3 \
  insurance-2023.html
```

### Example 2: Content Analysis
```bash
# Analyze content from specific author with statistics
python3 wp-exporter.py wordpress.xml \
  --author "john-doe" \
  --stats \
  --min-length 300 \
  john-content-analysis.html
```

### Example 3: Markdown Export for Documentation
```bash
# Export top 5 categories to Markdown for documentation
python3 wp-exporter.py wordpress.xml \
  --format markdown \
  --cat 5 \
  --clean \
  --branding "Company Documentation" \
  documentation.md
```

### Example 4: Category Discovery and Selection
```bash
# First, discover available categories
python3 wp-exporter.py wordpress.xml --list-categories

# Then extract specific categories based on results
python3 wp-exporter.py wordpress.xml \
  --categories "Insurance,Financial Planning,Retirement" \
  --stats \
  --clean \
  financial-content.html
```

### Example 5: Custom Styled Export
```bash
# Export with custom styling and branding
python3 wp-exporter.py wordpress.xml \
  --css company-branding.css \
  --branding "Acme Financial Blog" \
  --cat 5 \
  --clean \
  styled-blog.html
```

## Output Features

### HTML Output
- 📱 **Responsive Design**: Works on desktop and mobile
- 🎨 **Modern Styling**: Clean, professional appearance
- 🔍 **Interactive Index**: Click to navigate to articles
- 📄 **Print-Friendly**: Each article starts on new page
- ⬆️ **Easy Navigation**: Back to index buttons

### Markdown Output
- 📝 **Clean Formatting**: Proper headings and paragraphs
- 🔗 **Internal Links**: Clickable table of contents
- 📚 **Documentation Ready**: Perfect for knowledge bases
- 🔄 **Portable**: Works with any Markdown editor

### Statistics
- 📊 **Word Count Analysis**: Total, average, min/max
- ⏱️ **Reading Time**: Estimates based on 200 WPM
- 📈 **Category Distribution**: Most popular categories
- ✍️ **Author Contributions**: Article count by author
- 📅 **Publication Timeline**: Date range analysis

## Supported WordPress Elements

- ✅ **Posts**: Published blog posts only
- ✅ **Titles**: Article titles and headings
- ✅ **Content**: Full article content with formatting
- ✅ **Categories**: WordPress categories
- ✅ **Tags**: WordPress post tags
- ✅ **Authors**: Post author information
- ✅ **Dates**: Publication dates
- ✅ **Excerpts**: Post excerpts when available
- ✅ **Shortcodes**: Fusion Builder and other plugin shortcodes (with --clean)

## File Format Support

### Input
- **WordPress XML Export**: Standard WordPress export files
- **File Extension**: `.xml`

### Output
- **HTML**: Standalone HTML files (`.html`)
- **Markdown**: Standard Markdown files (`.md`)

## Tips and Best Practices

### 1. Discover Categories First
```bash
# Always check available categories before filtering
python3 wp-exporter.py wordpress.xml --list-categories
```

### 2. Use Date Ranges for Large Exports
```bash
# Break large exports into manageable chunks
python3 wp-exporter.py wordpress.xml --date-range 2023-01-01,2023-06-30
python3 wp-exporter.py wordpress.xml --date-range 2023-07-01,2023-12-31
```

### 3. Clean Plugin Shortcodes
```bash
# Always use --clean for cleaner output
python3 wp-exporter.py wordpress.xml --clean
```

### 4. Combine Features for Powerful Filtering
```bash
# Multiple filters work together
python3 wp-exporter.py wordpress.xml \
  --author "john" \
  --categories "Insurance" \
  --date-range 2023-01-01,2024-12-31 \
  --min-length 500 \
  --clean \
  --stats
```

### 5. Use Statistics for Content Planning
```bash
# Analyze your content before export
python3 wp-exporter.py wordpress.xml --stats --list-categories
```

## Troubleshooting

### Common Issues

1. **"File does not exist" error**
   - Check that the XML file path is correct
   - Use absolute paths if needed

2. **"No articles found"**
   - Ensure the XML contains published posts
   - Check if posts are in "draft" status instead of "publish"

3. **"Invalid date format"**
   - Use YYYY-MM-DD format for dates
   - Example: `2023-01-01,2024-12-31`

4. **Large file processing**
   - Use date range filtering to process in chunks
   - Consider filtering by categories to reduce size

### Performance Tips

- **Large XML files**: Use date range filtering to process in batches
- **Memory usage**: Filter early to reduce processing load
- **Output size**: Use specific category filtering for targeted exports

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit issues and enhancement requests.

## Version History

- **v1.0.0**: Initial release with core functionality
- **v1.1.0**: Added advanced filtering and statistics
- **v1.2.0**: Added Markdown export and custom styling
- **v1.3.0**: Added category discovery and enhanced UI
