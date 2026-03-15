---
name: "chinese-thesis-generator"
description: "Generates Chinese undergraduate thesis structures and content. Invoke when user asks for thesis help, outlines, or drafts."
---

# Chinese Undergraduate Thesis Generator Skill

This skill assists in the creation of standard Chinese undergraduate theses (本科毕业论文). It covers topic selection, outlining, drafting content, and formatting guidance.

## When to Use

Invoke this skill when the user:
- Asks for help writing a thesis.
- Requests a thesis outline or structure.
- Needs content generation for specific chapters (Introduction, Literature Review, etc.).
- Wants formatting advice for academic papers.

## Standard Thesis Structure (Reference)

1.  **封面 (Cover)**: Title, Student Name, ID, Major, Supervisor, Date.
2.  **摘要 (Abstract)**: Both Chinese and English. Includes Keywords.
3.  **目录 (Table of Contents)**: Generated automatically in Word.
4.  **正文 (Main Body)**:
    *   **第一章 绪论 (Chapter 1: Introduction)**: Research background, significance, status quo (literature review), research content and methods.
    *   **第二章 相关理论/技术 (Chapter 2: Theoretical Basis/Technology)**: Explanation of core concepts or technologies used.
    *   **第三章 需求分析 (Chapter 3: Requirements Analysis)**: Feasibility analysis, system requirements, use case diagrams.
    *   **第四章 系统设计 (Chapter 4: System Design)**: Architecture design, database design, module design.
    *   **第五章 系统实现 (Chapter 5: System Implementation)**: Key code logic, interface display, core algorithms.
    *   **第六章 系统测试 (Chapter 6: System Testing)**: Test environment, test cases (functional/performance), test analysis.
    *   **第七章 总结与展望 (Chapter 7: Conclusion & Future Work)**: Summary of achievements and future improvements.
5.  **参考文献 (References)**: Standard format (GB/T 7714).
6.  **致谢 (Acknowledgements)**: Formal expression of gratitude.
7.  **附录 (Appendix)**: Optional (code snippets, large tables).

## Capabilities

### 1. Topic & Outline Generation
Help the user refine a broad topic into a specific, researchable title. Generate a detailed chapter-level outline based on the chosen topic.

### 2. Content Drafting
Draft content for specific sections. Ensure academic tone:
- **Language**: Formal Chinese (书面语), avoid colloquialisms.
- **Style**: Objective, logical, data-driven.
- **Citations**: Remind user to insert citations [1].

### 3. Formatting Guidance (General)
- **Font**: Songti (宋体) for Chinese, Times New Roman for English/Numbers.
- **Size**: Title (Heiti 2/3), Headings (Heiti 4), Body (Songti Xiaosi - 12pt).
- **Line Spacing**: Usually 1.25 or 1.5 times.

## Interaction with Other Skills

- **Use `word` skill**: After generating content, offer to save the draft or outline to a `.docx` file using the `word` skill. This provides a tangible output for the user.
- **Use `pdf` skill**: If the user provides reference PDFs, use the `pdf` skill to extract relevant literature for the review section.

## Example Workflow

1.  **User**: "Help me write a thesis about AI in healthcare."
2.  **Agent**: "Here are 3 specific titles... Which one do you prefer?"
3.  **User**: "The second one."
4.  **Agent**: "Great. Here is a proposed outline for 'Application of Deep Learning in Medical Image Diagnosis'..."
5.  **User**: "Looks good. Write the Introduction."
6.  **Agent**: Generates Introduction text... "Would you like me to save this to `thesis_draft.docx`?"
7.  **User**: "Yes."
8.  **Agent**: Invokes `word` skill to save the file.
