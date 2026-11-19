.PHONY: release
release:
	@archive=$$(mktemp -d); \
		trap 'rm -rf "$$archive"' EXIT; \
		zip -q -r "$$archive/gopass.alfredworkflow" info.plist icon.png Gopass.alfredui -x '*/__pycache__/*' '*/.DS_Store' && \
		mv "$$archive/gopass.alfredworkflow" ../gopass.alfredworkflow
