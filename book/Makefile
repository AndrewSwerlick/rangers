# Makefile for TTRPG Rulebook
# Based on the LaTeX + Pandoc workflow

# Main document name (without extension)
MAIN = rulebook

# LaTeX compiler
LATEX = pdflatex
LATEX_FLAGS = -interaction=nonstopmode -halt-on-error

# Pandoc settings for ePub
PANDOC = pandoc
PANDOC_FLAGS = --toc
COVER_IMAGE = cover.jpg
ifneq (,$(wildcard $(COVER_IMAGE)))
    PANDOC_FLAGS += --epub-cover-image=$(COVER_IMAGE)
endif

.PHONY: all pdf epub clean watch help

help:
	@echo "TTRPG Rulebook Build System"
	@echo "============================"
	@echo ""
	@echo "Available targets:"
	@echo "  make pdf        - Build PDF for print (paperback)"
	@echo "  make epub       - Build ePub for eReaders"
	@echo "  make all        - Build both PDF and ePub"
	@echo "  make watch      - Auto-rebuild PDF on changes"
	@echo "  make clean      - Remove build artifacts"
	@echo "  make help       - Show this help message"

all: pdf epub

# Build PDF for print version
pdf: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex
	@echo "Building PDF..."
	$(LATEX) $(LATEX_FLAGS) $(MAIN).tex
	$(LATEX) $(LATEX_FLAGS) $(MAIN).tex  # Run twice for TOC/references
	@echo "✓ PDF built: $(MAIN).pdf"

# Build ePub for digital version
epub: $(MAIN).epub

$(MAIN).epub: $(MAIN).tex
	@echo "Building ePub..."
	$(PANDOC) $(PANDOC_FLAGS) $(MAIN).tex -o $(MAIN).epub
	@echo "✓ ePub built: $(MAIN).epub"

# Auto-rebuild on file changes (requires latexmk)
watch:
	latexmk -pdf -pvc $(MAIN).tex

# Clean build artifacts
clean:
	rm -f *.aux *.log *.toc *.out *.lot *.lof *.bbl *.blg *.bcf *.run.xml *.fls *.fdb_latexmk *.synctex.gz
	rm -f $(MAIN).pdf $(MAIN).epub
	@echo "✓ Cleaned build artifacts"
