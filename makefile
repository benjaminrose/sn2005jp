## Calibartiong Gemini F2 Obs of SN 2005jp host
## =============================================

.DEFAULT_GOAL := help
.PHONY: help cal clean all

clean: ## Remove non-original files
	trash SN2005jp*.fits
	trash cal/super*.fits
	trash cal/hot_pixels.fits
	
run: *.py ## Runs the main script
	python super_darks.py
	python master_flats.py
	python calibration.py
	
all: clean run  ## Executes clean then run


help:  ## Displays this message
	@echo "Commands for the image ccalibration"
	@echo "Use -B or --always-make to force all dependencies to rerun."
	@echo "Use -i or --ignore-errors to run all sub-commands, even if one fails"
	@echo " "
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'
