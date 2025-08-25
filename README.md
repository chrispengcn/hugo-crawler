# Blog Content Crawler

A Python script to crawl web content and convert it into Markdown files suitable for static site generators like Hugo. The script extracts specified content fields using XPath, handles image downloads, and maintains proper file organization.

Created by [HugoCMS](https://hugocms.net).
[Xpath Check Tool](https://aiwriter.shopaii.net/xpath.html)

## Features

- **Config-driven Extraction**: Define content fields (title, images, body, etc.) using XPath in a JSON configuration file
- **Image Handling**: 
  - Download images (JPG, PNG, GIF, WebP) and save to local directory
  - Automatic renaming with random 8-character suffix if file already exists
  - Configurable image download settings per content field
- **Duplicate Protection**: Skips already downloaded URLs using a log file
- **Markdown Generation**: Converts HTML content to Markdown with proper front matter
- **SEO-friendly Filenames**: Generates clean, sanitized filenames based on content titles
- **Error Logging**: Detailed logging for troubleshooting extraction and download issues

## Requirements

- Python 3.7+
- Required packages:
  ```
  requests
  beautifulsoup4
  lxml
  markdownify
  ```

## Installation

1. Clone or download this repository
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Prepare Configuration File**  
   Create a JSON configuration file (e.g., `config.json`) specifying:
   - Project root directory
   - Fields to extract (with XPath queries and attributes)
   - Image download preferences

2. **Create URL List**  
   Create a `urllist.txt` file in your project root directory containing one URL per line (URLs to crawl)

3. **Run the Script**  
   ```bash
   python crawler-json.py /path/to/your/config.json
   ```

## Configuration File Structure

The configuration file defines how content should be extracted and organized:

```json
{
  "project_root": "my_blog_project",
  "fields": {
    "FIELD_NAME": {
      "xpath": "XPATH_QUERY",
      "attribute": "ATTRIBUTE_TO_EXTRACT",
      "front_matter": true|false,
      "download_image": true|false
    }
  }
}
```

### Configuration Parameters

- `project_root`: Root directory for your blog project
- `fields`: Object containing content fields to extract
  - `xpath`: XPath query to locate the element
  - `attribute`: Attribute to extract ("text", "html", or specific attribute like "datetime")
  - `front_matter`: Whether to include this field in Markdown front matter
  - `download_image`: Whether to download images for this field (applies to image fields)

### Required Fields

- `title`: Main title of the content
- `content`: Main body content of the page

## Project Structure

After running the script, your project directory will have this structure:

```
project_root/
├── content/
│   └── blog/
│       └── YYYY-MM-DD-sanitized-title.md  # Generated Markdown files
├── static/
│   └── images/                            # Downloaded images
├── urllist.txt                            # List of URLs to crawl
└── downloaded.log                         # Log of processed URLs
```

## Example Workflow

1. Create project directories:
   ```bash
   mkdir -p my_blog_project/{content/blog,static/images}
   ```

2. Add URLs to `my_blog_project/urllist.txt`

3. Create and configure `config.json`

4. Run the crawler:
   ```bash
   python crawler-json.py config.json
   ```

## Notes

- The script respects `robots.txt` and includes a standard user-agent string
- Add a delay (uncomment `time.sleep(1)` in main loop) if you need to be more polite to servers
- Image downloads can be disabled per field using `download_image: false`
- All generated filenames are sanitized for SEO and filesystem compatibility

## License

MIT License - Feel free to modify and use this script according to your needs.
