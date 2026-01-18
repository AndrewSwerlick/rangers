{
  description = "TTRPG Rulebook Development Environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };

        # Comprehensive LaTeX distribution for professional book publishing
        tex = pkgs.texlive.combine {
          inherit (pkgs.texlive)
            # Core schemes - includes most standard packages
            scheme-medium

            # Additional document classes for book publishing
            memoir

            # Additional fonts
            cm-super

            # Additional utilities
            latexmk;
        };

      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # LaTeX distribution
            tex

            # Pandoc for ebook generation
            pandoc

            # PDF utilities
            ghostscript

            # Image processing (often needed for book covers/figures)
            imagemagick

            # Build automation
            gnumake

            # Shell utilities
            coreutils
            findutils

            # Git for version control
            git
          ];

          shellHook = ''
            echo "🎲 TTRPG Rulebook Development Environment"
            echo "=================================="
            echo "LaTeX: $(latex --version | head -n1)"
            echo "Pandoc: $(pandoc --version | head -n1)"
            echo ""
            echo "Your book files should go in the './book' directory"
            echo ""
            echo "Useful commands:"
            echo "  - pdflatex <file>.tex     # Compile LaTeX to PDF"
            echo "  - latexmk -pdf <file>.tex # Compile with automatic rebuilds"
            echo "  - pandoc <file>.tex -o <file>.epub # Convert to ePub"
            echo ""
          '';
        };
      }
    );
}
