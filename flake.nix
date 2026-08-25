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
            latexmk

            # XeLaTeX and LuaLaTeX support
            xetex
            luatex
            fontspec
            xunicode
            luaotfload

            # Additional packages for character sheet
            xcolor
            pgf  # TikZ
            ;
        };

        # Python environment for the OSM -> traceable park-map pipeline
        # (scripts/build_reference.py). Kept in its own devShell so it does
        # not perturb the LaTeX/Pandoc book toolchain above.
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          osmnx        # OpenStreetMap download + street-network modelling
          networkx     # graph topology (bridges, betweenness, ...)
          geopandas    # geospatial dataframes
          matplotlib   # PDF rendering
          shapely      # geometry
          rtree        # spatial index backing geopandas sjoin / sindex
        ]);

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

            # Google Fonts for typography (Josefin Sans, EB Garamond, Caveat)
            google-fonts

            # Fontconfig for font discovery
            fontconfig
          ];

          shellHook = ''
            # Set up font paths for XeLaTeX to find Google Fonts
            export OSFONTDIR="${pkgs.google-fonts}/share/fonts/truetype"

            # Create fontconfig configuration for XeLaTeX
            export FONTCONFIG_FILE=$(mktemp)
            cat > "$FONTCONFIG_FILE" << EOF
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <dir>${pkgs.google-fonts}/share/fonts/truetype</dir>
  <cachedir>/tmp/fontconfig-cache</cachedir>
</fontconfig>
EOF
            mkdir -p /tmp/fontconfig-cache
            fc-cache -f 2>/dev/null || true

            echo "🎲 TTRPG Rulebook Development Environment"
            echo "=================================="
            echo "LaTeX: $(latex --version | head -n1)"
            echo "XeLaTeX: $(xelatex --version | head -n1)"
            echo "Pandoc: $(pandoc --version | head -n1)"
            echo ""
            echo "Your book files should go in the './book' directory"
            echo ""
            echo "Useful commands:"
            echo "  - lualatex <file>.tex     # Compile with LuaLaTeX (recommended for variable fonts)"
            echo "  - xelatex <file>.tex      # Compile with XeLaTeX (system fonts)"
            echo "  - pdflatex <file>.tex     # Compile LaTeX to PDF (no system fonts)"
            echo "  - latexmk -lualatex <file>.tex # LuaLaTeX with automatic rebuilds"
            echo "  - pandoc <file>.tex -o <file>.epub # Convert to ePub"
            echo ""
            echo "Fonts available: Josefin Sans, EB Garamond, Caveat (Google Fonts variable fonts)"
            echo ""
          '';
        };

        # Separate shell for the geospatial map pipeline:
        #   nix develop .#python
        #   python scripts/build_reference.py --out out/hard_labor_creek
        devShells.python = pkgs.mkShell {
          buildInputs = [ pythonEnv pkgs.git ];
          shellHook = ''
            echo "🗺  Park-map reference environment (osmnx pipeline)"
            echo "=================================================="
            echo "Python: $(python --version)"
            python -c "import osmnx; print('OSMnx:', osmnx.__version__)"
            echo ""
            echo "Run: python scripts/build_reference.py --out out/hard_labor_creek"
            echo ""
          '';
        };

        # Image-only shell for the hand-traced-sketch -> wall-map pipeline
        # (scripts/build_playmap.sh). Deliberately excludes the LaTeX
        # toolchain so it loads fast when you are just iterating on a map.
        devShells.map = pkgs.mkShell {
          buildInputs = with pkgs; [
            imagemagick   # clean-up, enlargement, tiling
            ghostscript   # PDF assembly
            potrace       # bitmap -> vector, so enlargement stays crisp
            dejavu_fonts  # sheet labels on the tiled output
            coreutils
            gnumake
          ];
          shellHook = ''
            export PLAYMAP_FONT="${pkgs.dejavu_fonts}/share/fonts/truetype/DejaVuSans.ttf"
            echo "🗺  Play-map post-processing environment"
            echo "======================================="
            echo "ImageMagick: $(magick -version | head -n1 | cut -d' ' -f1-3)"
            echo "potrace:     $(potrace --version | head -n1)"
            echo ""
            echo "Run: ./scripts/build_playmap.sh map-images/hard-labor-sketch.jpg"
            echo ""
          '';
        };
      }
    );
}
