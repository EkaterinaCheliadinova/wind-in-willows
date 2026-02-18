PORT ?= 3000
HOST ?= 127.0.0.1
PYTHON ?= $(shell command -v python3 >/dev/null 2>&1 && echo python3 || echo python)
DRIVE_ROOT_ID ?= 1wSbweAapltIgdjl-Fs9oeKcsQpsi9eUt
THUMB_SIZE ?= 900
MAX_IMAGE_EDGE ?= 1600
JPEG_QUALITY ?= 86
SYNC_FLAGS ?= --skip-videos --wipe-output --thumb-size $(THUMB_SIZE) --max-image-edge $(MAX_IMAGE_EDGE) --jpeg-quality $(JPEG_QUALITY) --thumbs-only

.PHONY: run serve sync-kittens install-drive-deps regen-descriptions

run: serve

serve:
	@echo "Serving site at http://$(HOST):$(PORT)"
	@$(PYTHON) -m http.server $(PORT) --bind $(HOST)

sync-kittens:
	@$(PYTHON) sync_kittens_from_drive.py $(if $(DRIVE_ROOT_ID),--root-folder-id $(DRIVE_ROOT_ID),) $(SYNC_FLAGS)

install-drive-deps:
	@$(PYTHON) -m pip install -r requirements-drive.txt

regen-descriptions:
	@$(PYTHON) regenerate_descriptions.py
