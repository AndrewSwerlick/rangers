# TTRPG Rulebook Project

A professional book publishing setup using LaTeX and Pandoc for creating both print (PDF) and digital (ePub) versions of your TTRPG rulebook.

## Quick Start

### Enter the Development Environment

```bash
nix develop
```

This will load all necessary tools including LaTeX, Pandoc, and build utilities.

### Build Your Book

```bash
cd book

# Build PDF for print
make pdf

# Build ePub for eReaders
make epub

# Build both formats
make all

# Auto-rebuild PDF on changes
make watch
```

## Project Structure

```
.
├── flake.nix          # Nix development environment
├── book/              # Your book source files
│   ├── rulebook.tex   # Main LaTeX document
│   ├── Makefile       # Build automation
│   └── cover.jpg      # Cover image for ePub (add your own)
└── README.md          # This file
```

## Workflow

Based on the workflow described in [this blog post](http://theroadchoseme.com/how-i-self-published-a-professional-paperback-and-ebook-using-latex-and-pandoc):

1. **Write** your content in LaTeX (`book/rulebook.tex`)
2. **Build PDF** for print version with `make pdf`
3. **Build ePub** for digital version with `make epub`
4. **Publish** to Amazon KDP, Apple Books, or other platforms

### PDF (Print Version)

The PDF is generated using LaTeX with precise control over typography, layout, and print specifications. Perfect for:
- Amazon Kindle Direct Publishing (KDP) paperback
- Professional print-on-demand services
- High-quality PDF downloads

### ePub (Digital Version)

The ePub is generated using Pandoc from your LaTeX source. Compatible with:
- Amazon Kindle (upload .epub directly, or convert to .mobi)
- Apple Books
- Kobo
- Any standard eReader

## Customization

### Page Size and Margins

Edit the `\geometry` settings in `book/rulebook.tex`:

```latex
\geometry{
  paperwidth=6in,      % Customize for your trim size
  paperheight=9in,
  margin=0.75in,
  top=1in,
  bottom=1in
}
```

Common print sizes:
- 6" × 9" (standard trade paperback)
- 5.5" × 8.5" (digest size)
- 8.5" × 11" (US Letter)

### Cover Image

Add a `book/cover.jpg` file for your ePub cover image.

## Tools Included

- **LaTeX** - Professional typesetting system
- **Pandoc** - Universal document converter
- **latexmk** - Automated LaTeX building
- **ImageMagick** - Image processing
- **Ghostscript** - PDF utilities

## Tips

- Use `make watch` during writing for live PDF preview
- Run LaTeX twice to ensure table of contents and references update
- Keep images in a subdirectory (e.g., `book/images/`)
- Test your ePub on multiple devices before publishing

## Publishing Platforms

- **Amazon KDP**: https://kdp.amazon.com
- **Apple Books**: https://books.apple.com/us/author
- **Draft2Digital**: https://draft2digital.com
- **IngramSpark**: https://www.ingramspark.com

## Resources

- [Original blog post](http://theroadchoseme.com/how-i-self-published-a-professional-paperback-and-ebook-using-latex-and-pandoc)
- [LaTeX Documentation](https://www.latex-project.org/)
- [Pandoc Manual](https://pandoc.org/MANUAL.html)
