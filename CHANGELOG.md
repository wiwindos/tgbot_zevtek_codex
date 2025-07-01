# Changelog

## Unreleased

### Added
- Multimodal file support (Gemini)
- Graceful error handling with inline model picker
- `/admin errors` summary
- Automatic warning when context exceeds 1000 characters

### Changed
- All provider calls go through `safe_generate()`

### Fixed
- Graceful oversize file rejection
