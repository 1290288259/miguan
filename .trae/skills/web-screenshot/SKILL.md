---
name: "web-screenshot"
description: "Captures screenshots of web pages using Playwright. Invoke when user wants to screenshot the running application or websites for documentation."
---

# Web Screenshot Skill

This skill allows the agent to capture screenshots of web pages, which is useful for generating documentation, verifying UI changes, or creating visual reports.

## Prerequisites

- `playwright` python package must be installed.
- Playwright browsers must be installed (`playwright install chromium`).

## Capabilities

1.  **Full Page Screenshot**: Capture the entire scrollable area of a webpage.
2.  **Viewport Screenshot**: Capture only the visible area.
3.  **Element Screenshot**: Capture a specific element (by selector).

## Usage

Use the `RunCommand` tool to execute a Python script that uses `playwright.sync_api`.

### Example: Taking a screenshot of a URL

```python
from playwright.sync_api import sync_playwright

def take_screenshot(url, output_path="screenshot.png"):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        # Wait for network idle to ensure page is loaded
        page.wait_for_load_state("networkidle")
        page.screenshot(path=output_path, full_page=True)
        browser.close()
        print(f"Screenshot saved to {output_path}")

take_screenshot("http://localhost:5000")
```

### Integration with Word Skill

After taking screenshots, you can use the `word` skill to insert them into a document:

```python
from docx import Document
from docx.shared import Inches

doc = Document("report.docx")
doc.add_heading("System Screenshot", level=1)
doc.add_picture("screenshot.png", width=Inches(6))
doc.save("report_with_images.docx")
```
