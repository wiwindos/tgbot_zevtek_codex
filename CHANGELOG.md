# Changelog

## Unreleased

### Added
- Multimodal file support (Gemini)
- Graceful error handling with inline model picker
- `/admin errors` summary

### Changed
- All provider calls go through `safe_generate()`

### Fixed
- Graceful oversize file rejection
