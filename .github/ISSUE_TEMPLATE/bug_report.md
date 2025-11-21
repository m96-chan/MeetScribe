---
name: Bug Report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

# Bug Report

## Description
<!-- A clear and concise description of what the bug is -->

## Expected Behavior
<!-- What should happen -->

## Actual Behavior
<!-- What actually happens -->

## Steps to Reproduce
<!-- Detailed steps to reproduce the behavior -->

1.
2.
3.
4.

## Environment
<!-- Please complete the following information -->

- OS: [e.g. Windows 11, Ubuntu 22.04, macOS Ventura]
- Python Version: [e.g. 3.11.5]
- MeetScribe Version/Commit: [e.g. v0.1.0 or commit hash]
- Installation Method: [e.g. pip install, Docker, source]

## Configuration
<!-- If applicable, share relevant configuration (redact sensitive data) -->

```yaml
# Paste relevant config.yaml sections here
```

## Logs and Error Messages
<!-- Include relevant log output and error messages -->

```
Paste error messages and logs here
```

## TDD Context
<!-- Help us write tests to prevent regression -->

### Failing Test Case
<!-- If you can, describe what a test case would look like for this bug -->

```python
# Example test that should pass but currently fails
def test_bug_reproduction():
    # Setup

    # Action

    # Assert (what should happen)
    pass
```

### Root Cause (if known)
<!-- If you've identified the root cause, describe it here -->

### Affected Components
<!-- Check all that apply -->

- [ ] INPUT layer (recording providers)
- [ ] CONVERT layer (transcription)
- [ ] LLM layer (minutes generation)
- [ ] OUTPUT layer (rendering)
- [ ] Core (runner, daemon, config)
- [ ] CLI
- [ ] Documentation
- [ ] Other: ___________

## Additional Context
<!-- Add any other context about the problem here -->

### Screenshots
<!-- If applicable, add screenshots to help explain your problem -->

### Related Issues
<!-- Link to related issues if any -->

### Workaround
<!-- If you found a temporary workaround, describe it here -->

## Severity
<!-- Rate the impact of this bug -->

- [ ] Critical (system crash, data loss, security issue)
- [ ] High (major feature broken, no workaround)
- [ ] Medium (feature partially broken, workaround exists)
- [ ] Low (minor issue, cosmetic)

## Reproducibility
<!-- How often can you reproduce this bug? -->

- [ ] Always (100% reproducible)
- [ ] Frequently (>50% of the time)
- [ ] Sometimes (<50% of the time)
- [ ] Rare (happened once or twice)

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
