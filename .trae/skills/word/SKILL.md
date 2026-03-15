---
name: "word"
description: "Handles Microsoft Word documents (.docx). Invoke when user wants to read, write, create, or modify Word files."
---

# Word Processing Skill

This skill allows the agent to interact with Microsoft Word documents using the `python-docx` library.

## Capabilities

1.  **Read**: Extract text from `.docx` files.
2.  **Write**: Create new `.docx` files with text, headings, and basic formatting.
3.  **Modify**: Append content to existing `.docx` files.

## Usage

When the user asks to perform operations on Word documents, use the `RunCommand` tool to execute Python scripts that utilize `python-docx`.

### Example: Reading a Word file

```python
from docx import Document

def read_docx(file_path):
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

print(read_docx('path/to/document.docx'))
```

### Example: Creating a Word file

```python
from docx import Document

doc = Document()
doc.add_heading('Document Title', 0)
doc.add_paragraph('A plain paragraph having some ')
doc.add_paragraph('bold', style='Strong')
doc.save('path/to/new_document.docx')
```
