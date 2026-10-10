---
name: taskflow-frontend-design
description: Establish and verify the visual design of a Taskflow task that creates or materially changes a user-facing interface. Use within the task's acceptance criteria and existing product design.
---

Treat the task file, SPEC.md and project architecture as the requirements. Preserve existing design systems and user choices. This skill supplies a design workflow; it does not depend on Anthropic's Frontend Design plugin.

Before changing the interface, inspect nearby screens, component conventions, tokens and available references. Choose a coherent direction for hierarchy, typography, spacing, color and interaction states. For an existing product, develop its current visual language. For new work, record the important design choices in the task's notes using the parent's normal assumption workflow.

Implement the required user flow, including applicable loading, empty, validation and failure states. Use the existing stack and assets. Check keyboard access, focus visibility, readable contrast and responsive behavior at representative narrow and wide widths.

When browser tooling is available, open the actual application, exercise the changed flow and inspect the rendered layouts. Compare against supplied references and correct visible problems. Use the project's frontend tests where appropriate. Record what was checked and any unavailable browser validation in the task's test report; never claim a visual check from code inspection alone.

Stay within the current task. The parent owns Taskflow state and quality-helper invocation. Follow the test-writer, reviewer and fixer workflow after implementation. Do not use this skill for backend-only work, infrastructure or non-visual refactoring.
