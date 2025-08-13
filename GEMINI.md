# Gemini CLI Software Engineering Guidelines

This document outlines the general guidelines for all software engineering tasks, ensuring adherence to best practices and user requirements.

## Core Mandates

-   **Regular Testing:** All changes must be thoroughly tested. Tests (`pytest` or equivalent project-specific testing framework) will be run frequently *after every logical change* to ensure no functionality is broken. *All relevant tests must be run* to ensure existing functionality is preserved, even if changes are localized.
-   **Frequent Git Commits:** Changes will be committed frequently with clear, descriptive commit messages. Each commit should represent a single, atomic step.
-   **Maintain Backward Compatibility:** All existing behavior and functionality of the codebase must be preserved unless explicitly agreed upon with the user.

## General Coding Rules

-   **Adherence to Style Guides:** Follow project-specific style guides (e.g., PEP 8 for Python) for naming conventions, formatting, and docstrings.
-   **Remove Unused Code:** Unused imports, variables, and dead code should be removed.
-   **Function Splitting:** Large or complex functions should be split into smaller, more manageable private helper functions where appropriate.

## Project Structure

-   The overall project structure should remain consistent with existing patterns. New files, such as interface definitions, should be placed logically within the existing hierarchy.

## Reporting

-   Upon completion of significant tasks, a concise report should be produced summarizing the work done, including any new files created or major changes implemented.
