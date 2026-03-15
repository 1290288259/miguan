---
name: "pdf"
description: "Handles PDF documents. Invoke when user wants to read, extract text, or manipulate PDF files."
---

# PDF Processing Skill

This skill allows the agent to interact with PDF documents using the `PyPDF2` library.

## Capabilities

1.  **Read**: Extract text from `.pdf` files.
2.  **Merge**: Combine multiple PDFs into one.
3.  **Split**: Split PDFs into separate pages or files.

## Usage

When the user asks to perform operations on PDF documents, use the `RunCommand` tool to execute Python scripts that utilize `PyPDF2`.

### Example: Reading a PDF file

```python
from PyPDF2 import PdfReader

reader = PdfReader("path/to/document.pdf")
text = ""
for page in reader.pages:
    text += page.extract_text() + "\n"
print(text)
```

### Example: Merging PDFs

```python
from PyPDF2 import PdfMerger

merger = PdfMerger()
for pdf in ["file1.pdf", "file2.pdf"]:
    merger.append(pdf)
merger.write("merged-pdf.pdf")
merger.close()
```
