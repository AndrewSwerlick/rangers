#!/usr/bin/env python3
"""Build a faint, print-and-trace park-map reference PDF from OpenStreetMap.

Stage 1 of a TTRPG map pipeline. This produces a *tracing guide* -- a light
US-Letter PDF that goes under paper and gets hand-inked, then discarded. It is
NOT final art. Its only jobs are to be correct (right topology) and followable
(clear enough to trace by hand).

The mechanically meaningful units downstream are junctions and points of
interest, not distance. So this script deliberately does NOT draw a grid,
distance ticks, or uniform segment spacing. The only legibility constraint it
enforces is a "don't overlap" check on POIs so a game token still fits between
any two of them.

Outputs (given `--out DIR/STEM`):
    STEM.pdf            the traceable reference
    STEM.graphml        the intermediate graph (reuse instead of re-hitting OSM)
    STEM.gpkg           same graph as a GeoPackage for GIS tools
    STEM.report.json    machine-readable topology / coverage report
    STEM.report.txt     the same, human-readable

Run inside the python devShell:
    nix develop .#python
    python scripts/build_reference.py --out out/hard_labor_creek
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: we only write files
import matplotlib.pyplot as plt
import networkx as nx
import osmnx as ox
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from shapely.geometry import LineString, MultiPolygon, Point, Polygon
from shapely.ops import linemerge, unary_union

# --------------------------------------------------------------------------- #
# Configuration                                                               #
# --------------------------------------------------------------------------- #

DEFAULT_PARK = "Hard Labor Creek State Park, Georgia, USA"

# highway= values we treat as trail vs road. Anything not in either set is
# reported as "unknown" so the human can decide.
TRAIL_HIGHWAYS = {
    "footway", "path", "track", "bridleway", "cycleway", "steps", "pedestrian",
}
ROAD_HIGHWAYS = {
    "service", "unclassified", "residential", "tertiary", "tertiary_link",
    "secondary", "secondary_link", "primary", "primary_link", "road",
    "living_street", "trunk", "trunk_link", "motorway", "motorway_link",
}

# Extra OSM way tags to retain so we can classify better and spot cart paths.
EXTRA_WAY_TAGS = [
    "golf", "surface", "access", "service", "tracktype", "designation",
    "foot", "bicycle", "horse", "motor_vehicle",
]

# Candidate POI tags. Keyed by OSM key; value is list of values (or True=any).
# We keep the matched key/value as the POI "type" plus its name.
POI_TAGS = {
    "amenity": ["parking", "shelter", "ranger_station", "toilets", "cafe",
                "restaurant", "bbq"],
    "tourism": ["information", "camp_site", "caravan_site", "picnic_site",
                "viewpoint", "attraction", "chalet", "wilderness_hut",
                "camp_pitch", "hotel", "motel"],
    "leisure": ["golf_course", "swimming_area", "beach_resort", "marina",
                "sports_centre", "picnic_table", "nature_reserve",
                "fishing", "stadium", "horse_riding"],
    "natural": ["beach", "peak"],
    "man_made": ["observatory", "telescope", "tower"],
    "building": ["cabin", "bungalow", "clubhouse"],
    "highway": ["trailhead"],
}

# Water is drawn as shaded polygons (not point POIs), so it reads as an actual
# body of water rather than a dot.
WATER_TAGS = {"natural": ["water"], "water": True, "landuse": ["reservoir"]}

# Linear waterways (creeks, rivers) are drawn as thin grey lines so streams
# like Rocky Creek / Hard Labor Creek show up, tied visually to the lakes.
WATERWAY_TAGS = {"waterway": ["stream", "river", "canal", "brook", "tidal_channel"]}

# Rendering palette. Tuned to survive a BLACK-AND-WHITE laser printer: every
# category is separable by grey value AND by line style/shape (dashes, dots,
# rings, triangles), so nothing depends on colour. Kept dark enough that a
# toner-based mono printer won't drop the light lines, while still reading as
# a base to trace over rather than final art.
COL_ROAD = "#2f2f2f"          # solid, near-black dark grey
COL_TRAIL = "#3d3d3d"         # dark too; told apart from roads by a wide dash
COL_UNKNOWN = "#7a5c2e"       # dotted; a mid grey when printed mono
COL_BUILDING = "#4a4a4a"      # building footprint outline
COL_WATER_FILL = "#8f8f8f"    # dark-enough shading to see water through paper
COL_WATER_EDGE = "#3f3f3f"    # strong shoreline + creek line to trace
COL_POI_TEXT = "#000000"

# Roads are solid; trails use a widely-spaced dash so the two stay distinct
# even though both are dark. Unclassified stays a tight dot pattern.
TRAIL_DASH = (0, (7, 5))
UNKNOWN_DASH = (0, (1, 2))
# No point markers are drawn (dots/triangles/rings are the tracer's to add).
# Every road gets a light-grey "casing" band drawn under the dark line, so a
# road reads as a cased double-line and is easy to tell from a dashed trail.
# Hue-free, so it survives a mono printer.
COL_ROAD_CASING = "#a8a8a8"   # light-grey casing under every road


# --------------------------------------------------------------------------- #
# 1. Boundary                                                                 #
# --------------------------------------------------------------------------- #

def fetch_boundary(park: str, osmid: str | None, allow_any: bool):
    """Resolve the park polygon and sanity-check it is the *park*.

    Returns (geom_4326, name, area_acres, osmid_str).
    """
    if osmid:
        gdf = ox.geocode_to_gdf(osmid, by_osmid=True)
    else:
        gdf = ox.geocode_to_gdf(park)

    row = gdf.iloc[0]
    geom = row.geometry
    name = str(row.get("display_name", park))
    osmid_str = f"{row.get('osm_type', '?')}/{row.get('osm_id', '?')}"

    # Area in acres, via an equal-area-ish local UTM projection.
    proj = ox.projection.project_gdf(gdf)
    area_m2 = float(proj.geometry.iloc[0].area)
    area_acres = area_m2 / 4046.8564224

    print("── Boundary ─────────────────────────────────────────────")
    print(f"  name : {name}")
    print(f"  osm  : {osmid_str}")
    print(f"  area : {area_acres:,.0f} acres ({area_m2/1e6:,.2f} km²)")
    print(f"  type : {geom.geom_type}")

    if not allow_any:
        low = name.lower()
        problems = []
        if not isinstance(geom, (Polygon, MultiPolygon)):
            problems.append(f"geometry is {geom.geom_type}, not a polygon")
        if "reservoir" in low and "state park" not in low:
            problems.append("name looks like the RESERVOIR, not the state park")
        if "hard labor creek" not in low:
            problems.append("name does not contain 'Hard Labor Creek'")
        if area_acres < 1000:
            problems.append(f"area {area_acres:,.0f} ac is too small for the "
                            "~5,800-acre park")
        if problems:
            print("\n  ⚠  This does not look like Hard Labor Creek STATE PARK:",
                  file=sys.stderr)
            for p in problems:
                print(f"       - {p}", file=sys.stderr)
            print("     Pass a known-good --osmid (e.g. 'R1234567') or "
                  "--allow-any to override.", file=sys.stderr)
            raise SystemExit(2)

    return geom, name, area_acres, osmid_str


# --------------------------------------------------------------------------- #
# 2-3. Network + classification                                               #
# --------------------------------------------------------------------------- #

def _as_list(v):
    return v if isinstance(v, list) else [v]


def classify_edge(data: dict) -> tuple[str, bool, list[str]]:
    """Return (kind, is_cart_path, unknown_highways).

    kind is 'road' | 'trail' | 'unknown'. Trail wins ties on multi-valued
    highway tags (mixed-use ways trace as trails).
    """
    hw_raw = data.get("highway")
    unknown: list[str] = []
    if hw_raw is None:
        return "unknown", False, unknown

    hws = [str(h) for h in _as_list(hw_raw)]
    is_trail = any(h in TRAIL_HIGHWAYS for h in hws)
    is_road = any(h in ROAD_HIGHWAYS for h in hws)
    for h in hws:
        if h not in TRAIL_HIGHWAYS and h not in ROAD_HIGHWAYS:
            unknown.append(h)

    if is_trail:
        kind = "trail"
    elif is_road:
        kind = "road"
    else:
        kind = "unknown"

    # Golf cart paths pollute park networks -- surface them for filtering.
    golf = data.get("golf")
    golf_vals = {str(g) for g in _as_list(golf)} if golf is not None else set()
    name = " ".join(str(n) for n in _as_list(data.get("name", ""))).lower()
    is_cart = ("cartpath" in golf_vals or "path" in golf_vals
               or "cart" in name)

    return kind, is_cart, unknown


def pull_network(polygon):
    """Download roads + trails inside the boundary, junction-to-junction."""
    ox.settings.useful_tags_way = sorted(
        set(ox.settings.useful_tags_way) | set(EXTRA_WAY_TAGS)
    )
    # network_type='all' keeps both roads and trails. truncate_by_edge keeps
    # edges that cross the boundary (so we can find entrances). retain_all
    # keeps disconnected trail fragments -- we do not prune editorially here.
    G = ox.graph_from_polygon(
        polygon,
        network_type="all",
        simplify=True,
        truncate_by_edge=True,
        retain_all=True,
    )
    return G


# --------------------------------------------------------------------------- #
# 5. Consolidate + project                                                    #
# --------------------------------------------------------------------------- #

def project_and_consolidate(G, tolerance: float):
    """Project to UTM, then merge near-coincident junctions.

    osmnx consolidation collapses complex/duplicated intersections to single
    nodes while keeping true edge geometry, so trails still look like trails
    when traced. tolerance<=0 disables it.
    """
    Gp = ox.project_graph(G)
    if tolerance and tolerance > 0:
        Gp = ox.consolidate_intersections(
            Gp, tolerance=tolerance, rebuild_graph=True,
            dead_ends=True, reconnect_edges=True,
        )
    return Gp


def annotate_edges(Gp):
    """Attach kind / cart-path flags; collect unknown highway types."""
    unknown_types: dict[str, int] = {}
    counts = {"road": 0, "trail": 0, "unknown": 0}
    cart_paths = 0
    for u, v, k, data in Gp.edges(keys=True, data=True):
        kind, is_cart, unknown = classify_edge(data)
        data["kind"] = kind
        data["cart_path"] = bool(is_cart)
        counts[kind] += 1
        if is_cart:
            cart_paths += 1
        for h in unknown:
            unknown_types[h] = unknown_types.get(h, 0) + 1
    return counts, unknown_types, cart_paths


# --------------------------------------------------------------------------- #
# 6. Topology                                                                  #
# --------------------------------------------------------------------------- #

def analyze_topology(Gp):
    """Bridges, edge betweenness, articulation points, entrances-ready graph.

    Attaches to edges: bridge_topo (bool), betweenness (float), choke (bool).
    Attaches to nodes: articulation (bool).
    Returns a dict of summary structures for the report.
    """
    # Collapse to a simple undirected graph for topology; keep min length so
    # betweenness weighting is sane. Remember which simple edge maps to which
    # multi-edges so we can push results back.
    UG = nx.Graph()
    simple_to_multi: dict[tuple, list[tuple]] = {}
    for u, v, k, data in Gp.edges(keys=True, data=True):
        if u == v:
            continue
        length = float(data.get("length", 1.0) or 1.0)
        key = (u, v) if u < v else (v, u)
        simple_to_multi.setdefault(key, []).append((u, v, k))
        if UG.has_edge(u, v):
            if length < UG[u][v]["length"]:
                UG[u][v]["length"] = length
        else:
            UG.add_edge(u, v, length=length)

    # Bridges (per connected component; nx handles disconnected graphs).
    bridge_set = set()
    for a, b in nx.bridges(UG):
        bridge_set.add((a, b) if a < b else (b, a))

    # Articulation points (cut vertices) -> node chokepoints.
    artic = set(nx.articulation_points(UG))

    # Edge betweenness centrality, length-weighted.
    ebc = nx.edge_betweenness_centrality(UG, weight="length", normalized=True)
    ebc = {((a, b) if a < b else (b, a)): c for (a, b), c in ebc.items()}

    # Chokepoint edges = bridges OR top-decile betweenness.
    if ebc:
        vals = sorted(ebc.values())
        thresh = vals[int(0.9 * (len(vals) - 1))]
    else:
        thresh = float("inf")

    # A tree-like park network makes *most* edges bridges, so "bridge OR top
    # decile" is the right set for the REPORT but far too dense to draw as a
    # light hint. For the on-map accent we keep only the strongest funnels:
    # the top few edges by betweenness. That keeps the red genuinely sparse.
    if ebc:
        vis_thresh = vals[int(0.88 * (len(vals) - 1))]
        vis_thresh = max(vis_thresh, sorted(vals)[-min(len(vals), 20)])
    else:
        vis_thresh = float("inf")

    choke_edges = []
    for key, multi in simple_to_multi.items():
        is_bridge = key in bridge_set
        cent = ebc.get(key, 0.0)
        is_choke = is_bridge or cent >= thresh
        is_choke_vis = cent >= vis_thresh and cent > 0
        for (u, v, k) in multi:
            d = Gp.edges[u, v, k]
            d["bridge_topo"] = bool(is_bridge)
            d["betweenness"] = float(cent)
            d["choke"] = bool(is_choke)
            d["choke_visual"] = bool(is_choke_vis)
        if is_choke:
            name = _edge_name(Gp, multi[0])
            choke_edges.append({
                "u": key[0], "v": key[1], "bridge": is_bridge,
                "betweenness": round(cent, 4), "name": name,
                "kind": Gp.edges[multi[0]].get("kind", "unknown"),
            })

    # Nodes to ring on the map: articulation points that actually sit on a
    # strongly-funnelling (visual) edge -- the ones worth the eye's attention.
    vis_nodes = set()
    for u, v, k, data in Gp.edges(keys=True, data=True):
        if data.get("choke_visual"):
            vis_nodes.add(u)
            vis_nodes.add(v)
    for n, data in Gp.nodes(data=True):
        data["articulation"] = bool(n in artic)
        data["choke_visual"] = bool(n in artic and n in vis_nodes)

    choke_edges.sort(key=lambda e: (not e["bridge"], -e["betweenness"]))
    return {
        "bridge_count": len(bridge_set),
        "articulation_points": len(artic),
        "chokepoints": choke_edges,
        "_UG": UG,
    }


def _edge_name(Gp, edge_key):
    d = Gp.edges[edge_key]
    n = d.get("name")
    if not n:
        return None
    return " / ".join(str(x) for x in _as_list(n))


def find_entrances(Gp, boundary_proj):
    """Nodes inside the park with a road edge crossing the boundary.

    Marks node attr 'entrance' and returns a list of entrance descriptors.
    """
    boundary_line = boundary_proj.boundary  # exterior + holes
    entrances = []
    seen = set()
    for u, v, k, data in Gp.edges(keys=True, data=True):
        geom = data.get("geometry")
        if geom is None:
            pu = Point(Gp.nodes[u]["x"], Gp.nodes[u]["y"])
            pv = Point(Gp.nodes[v]["x"], Gp.nodes[v]["y"])
            geom = LineString([pu, pv])
        if not geom.crosses(boundary_line) and not geom.intersects(boundary_line):
            continue
        # Only count a crossing if one endpoint is in and the other out.
        pu = Point(Gp.nodes[u]["x"], Gp.nodes[u]["y"])
        pv = Point(Gp.nodes[v]["x"], Gp.nodes[v]["y"])
        u_in = boundary_proj.contains(pu)
        v_in = boundary_proj.contains(pv)
        if u_in == v_in:
            continue
        inside_node = u if u_in else v
        if inside_node in seen:
            continue
        seen.add(inside_node)
        Gp.nodes[inside_node]["entrance"] = True
        entrances.append({
            "node": inside_node,
            "x": float(Gp.nodes[inside_node]["x"]),
            "y": float(Gp.nodes[inside_node]["y"]),
            "kind": data.get("kind", "unknown"),
            "name": _edge_name(Gp, (u, v, k)),
        })
    return entrances


def longest_road_path(Gp, UG):
    """Weighted diameter of the largest road component (approximate 'longest').

    A true longest simple path is NP-hard; the network diameter (longest
    shortest path) is the useful, computable proxy for "how far does the road
    spine reach".
    """
    road_edges = [(u, v) for u, v, d in Gp.edges(data=True)
                  if d.get("kind") == "road"]
    RG = nx.Graph()
    for u, v in road_edges:
        if UG.has_edge(u, v):
            RG.add_edge(u, v, length=UG[u][v]["length"])
    if RG.number_of_edges() == 0:
        return None
    comp = max(nx.connected_components(RG), key=len)
    sub = RG.subgraph(comp)
    # Double-sweep to approximate the weighted diameter cheaply.
    start = next(iter(sub.nodes))
    d1 = nx.single_source_dijkstra_path_length(sub, start, weight="length")
    far = max(d1, key=d1.get)
    d2 = nx.single_source_dijkstra_path_length(sub, far, weight="length")
    other = max(d2, key=d2.get)
    return {
        "from_node": far, "to_node": other,
        "length_m": round(d2[other], 1),
        "length_mi": round(d2[other] / 1609.344, 2),
        "component_nodes": sub.number_of_nodes(),
    }


# --------------------------------------------------------------------------- #
# 4. POIs                                                                      #
# --------------------------------------------------------------------------- #

def pull_pois(polygon, target_crs):
    """Fetch candidate POIs, project them, and return a list of dicts.

    Each: {x, y, name, poi_type}. Polygonal features become their centroid.
    """
    try:
        gdf = ox.features_from_polygon(polygon, POI_TAGS)
    except Exception as exc:  # noqa: BLE001 -- OSM can return nothing
        print(f"  ⚠  POI fetch returned nothing usable: {exc}", file=sys.stderr)
        return []

    if gdf.empty:
        return []

    gdf = gdf.to_crs(target_crs)
    pois = []
    for _, row in gdf.iterrows():
        poi_type = None
        for key in POI_TAGS:
            val = row.get(key)
            if val is not None and str(val) != "nan" and val == val:
                poi_type = f"{key}={val}"
                break
        if poi_type is None:
            continue
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        pt = geom if geom.geom_type == "Point" else geom.centroid
        name = row.get("name")
        if name is None or str(name) == "nan" or name != name:
            name = ""
        pois.append({
            "x": float(pt.x), "y": float(pt.y),
            "name": str(name), "poi_type": poi_type,
        })
    return pois


def pull_water(polygon, target_crs):
    """Fetch water bodies as polygons to shade. Returns list of (geom, name)."""
    try:
        gdf = ox.features_from_polygon(polygon, WATER_TAGS)
    except Exception as exc:  # noqa: BLE001 -- OSM can return nothing
        print(f"  ⚠  Water fetch returned nothing usable: {exc}",
              file=sys.stderr)
        return []
    if gdf.empty:
        return []
    gdf = gdf.to_crs(target_crs)
    out = []
    for _, row in gdf.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        if geom.geom_type not in ("Polygon", "MultiPolygon"):
            continue
        name = row.get("name")
        if name is None or str(name) == "nan" or name != name:
            name = ""
        out.append((geom, str(name)))
    return out


def pull_waterways(polygon, target_crs):
    """Fetch linear waterways (creeks/rivers) as lines. Returns list of geoms."""
    try:
        gdf = ox.features_from_polygon(polygon, WATERWAY_TAGS)
    except Exception as exc:  # noqa: BLE001 -- OSM can return nothing
        print(f"  ⚠  Waterway fetch returned nothing usable: {exc}",
              file=sys.stderr)
        return []
    if gdf.empty:
        return []
    gdf = gdf.to_crs(target_crs)
    lines = []
    for geom in gdf.geometry:
        if geom is None or geom.is_empty:
            continue
        if geom.geom_type in ("LineString", "MultiLineString"):
            lines.append(geom)
    return lines


def pull_buildings(polygon, target_crs):
    """Fetch building footprints for a more complete map to trace.

    Returns a list of projected shapely polygons (visitor center, cottages,
    clubhouse, bathhouses, shelters, etc.). These are drawn as thin outlines.
    """
    try:
        gdf = ox.features_from_polygon(polygon, {"building": True})
    except Exception as exc:  # noqa: BLE001 -- OSM can return nothing
        print(f"  ⚠  Building fetch returned nothing usable: {exc}",
              file=sys.stderr)
        return []
    if gdf.empty:
        return []
    gdf = gdf.to_crs(target_crs)
    polys = []
    for geom in gdf.geometry:
        if geom is None or geom.is_empty:
            continue
        if geom.geom_type in ("Polygon", "MultiPolygon"):
            polys.append(geom)
    return polys


def dedupe_pois(pois, min_sep_m):
    """Greedy 'don't overlap' cull: drop POIs closer than min_sep_m to a kept
    one. Named POIs are preferred over unnamed. This is a legibility check
    (fit a token between them), NOT a spacing rule."""
    ordered = sorted(pois, key=lambda p: (p["name"] == "", ))  # named first
    kept = []
    for p in ordered:
        ok = True
        for q in kept:
            if (p["x"] - q["x"]) ** 2 + (p["y"] - q["y"]) ** 2 < min_sep_m ** 2:
                ok = False
                break
        if ok:
            kept.append(p)
    return kept


# --------------------------------------------------------------------------- #
# 7. Render                                                                    #
# --------------------------------------------------------------------------- #

LETTER = (8.5, 11.0)  # inches


def choose_orientation(bbox, orientation):
    """Return (fig_w_in, fig_h_in) for US Letter, minimizing wasted paper."""
    minx, miny, maxx, maxy = bbox
    w, h = maxx - minx, maxy - miny
    map_aspect = w / h if h else 1.0

    def fit_scale(page_w, page_h):
        # inches available after margins are applied later; ratio only.
        return min(page_w / w, page_h / h)

    if orientation == "portrait":
        return LETTER
    if orientation == "landscape":
        return (LETTER[1], LETTER[0])
    # auto: pick the orientation giving the larger drawing scale.
    port = fit_scale(*LETTER)
    land = fit_scale(LETTER[1], LETTER[0])
    return LETTER if port >= land else (LETTER[1], LETTER[0])


def _edge_geom(Gp, u, v, k, data):
    geom = data.get("geometry")
    if geom is not None:
        return geom
    return LineString([
        (Gp.nodes[u]["x"], Gp.nodes[u]["y"]),
        (Gp.nodes[v]["x"], Gp.nodes[v]["y"]),
    ])


def place_labels(ax, pois, bbox, base_off):
    """Very light label de-collision: offset each label from its dot and nudge
    labels that share a coarse grid cell. Good enough for a tracing guide."""
    minx, miny, maxx, maxy = bbox
    occupied = {}
    cell = base_off * 2.2
    dirs = [(1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)]
    for p in pois:
        label = p["name"] if p["name"] else p["poi_type"].split("=")[-1]
        placed = False
        for dx, dy in dirs:
            lx = p["x"] + dx * base_off
            ly = p["y"] + dy * base_off
            cellkey = (round(lx / cell), round(ly / cell))
            if cellkey not in occupied:
                occupied[cellkey] = True
                ha = "left" if dx >= 0 else "right"
                ax.annotate(
                    label, xy=(p["x"], p["y"]), xytext=(lx, ly),
                    fontsize=4.8, color=COL_POI_TEXT, ha=ha, va="center",
                    zorder=6,
                )
                placed = True
                break
        if not placed:
            ax.annotate(
                label, xy=(p["x"], p["y"]),
                xytext=(p["x"] + base_off, p["y"] + base_off),
                fontsize=4.8, color=COL_POI_TEXT, ha="left", va="center",
                zorder=6,
            )


def label_trails(ax, Gp):
    """Label each named trail once, rotated along its path, so routes are
    identifiable while tracing. One label per distinct name (placed on its
    longest segment) keeps repeated multi-edge trails from spamming labels."""
    best = {}  # name -> (length, geom)
    for u, v, k, data in Gp.edges(keys=True, data=True):
        if data.get("kind") != "trail":
            continue
        name = data.get("name")
        if not name:
            continue
        nm = " / ".join(str(x) for x in _as_list(name))
        geom = _edge_geom(Gp, u, v, k, data)
        if nm not in best or geom.length > best[nm][0]:
            best[nm] = (geom.length, geom)

    for nm, (_length, geom) in best.items():
        mid = geom.interpolate(0.5, normalized=True)
        p1 = geom.interpolate(0.45, normalized=True)
        p2 = geom.interpolate(0.55, normalized=True)
        ang = math.degrees(math.atan2(p2.y - p1.y, p2.x - p1.x))
        if ang > 90:
            ang -= 180
        elif ang < -90:
            ang += 180
        ax.text(mid.x, mid.y, nm, fontsize=4.2, style="italic",
                color=COL_ROAD, ha="center", va="center", rotation=ang,
                rotation_mode="anchor", zorder=6,
                bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none",
                          alpha=0.6))


def render_pdf(Gp, boundary_proj, pois, water, waterways, buildings, park_name,
               out_pdf, orientation, margin_in, show_labels):
    # Fit tightly to what is actually drawn (network + water + creeks +
    # buildings), NOT the park boundary -- the boundary extends past the
    # features and would waste paper. This maximises the tracing size.
    bbox = _content_bbox(Gp, water, waterways, buildings)
    fig_w, fig_h = choose_orientation(bbox, orientation)

    fig = plt.figure(figsize=(fig_w, fig_h))
    # Push the drawing to the paper edge (minus a thin margin). The title is
    # floated in the top whitespace via fig.text instead of reserving a strip,
    # so it costs the map no space.
    mx = margin_in / fig_w
    my = margin_in / fig_h
    ax = fig.add_axes([mx, my, 1 - 2 * mx, 1 - 2 * my])
    ax.set_aspect("equal")
    ax.axis("off")

    # Water bodies, shaded, drawn first so everything else sits on top.
    for geom, _name in water:
        for poly in _iter_polys(geom):
            ax.fill(*poly.exterior.xy, facecolor=COL_WATER_FILL,
                    edgecolor=COL_WATER_EDGE, lw=0.9, zorder=0.5)
            for hole in poly.interiors:
                ax.fill(*hole.xy, facecolor="white", edgecolor=COL_WATER_EDGE,
                        lw=0.7, zorder=0.6)

    # Linear waterways (creeks/rivers) -- dark lines, stitched continuous.
    for geom in _merge_lines(waterways):
        _plot_line(ax, geom, color=COL_WATER_EDGE, lw=0.9, zorder=1.5)

    # Building footprints -- thin outlines so cottages/shelters/etc. can be
    # traced too, without competing with the road/trail network.
    for geom in buildings:
        for poly in _iter_polys(geom):
            xb, yb = poly.exterior.xy
            ax.plot(xb, yb, color=COL_BUILDING, lw=0.7, zorder=3.5)

    # Stitch contiguous same-type edges into continuous polylines before
    # drawing. Otherwise the dash pattern restarts on every short consolidated
    # edge and short trail segments render as solid. Merging lets a dash run
    # across the whole trail so trails read as dashed everywhere.
    by_kind = {"road": [], "trail": [], "unknown": []}
    for u, v, k, data in Gp.edges(keys=True, data=True):
        kind = data.get("kind", "unknown")
        if kind not in by_kind:
            kind = "unknown"
        by_kind[kind].append(_edge_geom(Gp, u, v, k, data))
    road_lines = _merge_lines(by_kind["road"])
    trail_lines = _merge_lines(by_kind["trail"])
    unknown_lines = _merge_lines(by_kind["unknown"])

    # Road casings first (grey band under every road), then all lines on top.
    for geom in road_lines:
        _plot_line(ax, geom, color=COL_ROAD_CASING, lw=3.4, zorder=2)
    for geom in road_lines:
        _plot_line(ax, geom, color=COL_ROAD, lw=1.3, zorder=3)
    for geom in trail_lines:
        _plot_line(ax, geom, color=COL_TRAIL, lw=1.0, ls=TRAIL_DASH, zorder=3)
    for geom in unknown_lines:
        _plot_line(ax, geom, color=COL_UNKNOWN, lw=0.9, ls=UNKNOWN_DASH,
                   zorder=3)

    # Text labels are off by default -- names crowd the linework you trace over.
    # Turn them on with --labels. POI + water-body names, then trail names.
    if show_labels:
        span = max(bbox[2] - bbox[0], bbox[3] - bbox[1])
        label_pts = list(pois)
        for geom, name in water:
            if name:
                c = geom.centroid
                label_pts.append({"x": float(c.x), "y": float(c.y),
                                  "name": name, "poi_type": "natural=water"})
        place_labels(ax, label_pts, bbox, base_off=span * 0.012)
        label_trails(ax, Gp)

    ax.set_xlim(bbox[0], bbox[2])
    ax.set_ylim(bbox[1], bbox[3])
    _add_legend(ax, bool(buildings))
    fig.text(0.5, 1 - (margin_in / fig_h) * 0.5,
             f"{park_name}  —  tracing reference (not final art)",
             ha="center", va="center", fontsize=6.5, color="#333")

    fig.savefig(out_pdf, format="pdf", dpi=300)
    plt.close(fig)


def _content_bbox(Gp, water, waterways, buildings):
    """Bounding box of everything actually drawn, so the frame hugs the map."""
    xs = [d["x"] for _, d in Gp.nodes(data=True)]
    ys = [d["y"] for _, d in Gp.nodes(data=True)]
    minx, miny, maxx, maxy = min(xs), min(ys), max(xs), max(ys)
    for g in [w[0] for w in water] + list(waterways) + list(buildings):
        gx0, gy0, gx1, gy1 = g.bounds
        minx, miny = min(minx, gx0), min(miny, gy0)
        maxx, maxy = max(maxx, gx1), max(maxy, gy1)
    return (minx, miny, maxx, maxy)


def _iter_polys(geom):
    if isinstance(geom, MultiPolygon):
        return list(geom.geoms)
    if isinstance(geom, Polygon):
        return [geom]
    return []


def _plot_line(ax, geom, **kw):
    parts = geom.geoms if geom.geom_type == "MultiLineString" else [geom]
    for part in parts:
        x, y = part.xy
        ax.plot(x, y, **kw)


def _merge_lines(geoms):
    """Stitch contiguous line segments into the longest possible polylines, so
    a dash pattern runs continuously instead of restarting per graph edge."""
    if not geoms:
        return []
    merged = linemerge(unary_union(geoms))
    if merged.is_empty:
        return []
    return list(merged.geoms) if merged.geom_type == "MultiLineString" \
        else [merged]


def _add_legend(ax, has_buildings):
    handles = [
        Line2D([0], [0], color=COL_ROAD, lw=1.3, label="road"),
        Line2D([0], [0], color=COL_TRAIL, lw=1.0, ls=TRAIL_DASH,
               label="trail"),
        Line2D([0], [0], color=COL_UNKNOWN, lw=0.9, ls=UNKNOWN_DASH,
               label="unclassified"),
        Patch(facecolor=COL_WATER_FILL, edgecolor=COL_WATER_EDGE, label="water"),
        Line2D([0], [0], color=COL_WATER_EDGE, lw=0.9, label="creek/stream"),
    ]
    if has_buildings:
        handles.append(
            Line2D([0], [0], color=COL_BUILDING, lw=0.7, label="building"))
    leg = ax.legend(handles=handles, loc="lower left", fontsize=5.0,
                    frameon=True, framealpha=0.7, title=None)
    leg.set_zorder(10)


# --------------------------------------------------------------------------- #
# 8. Save graph + report                                                      #
# --------------------------------------------------------------------------- #

def save_graph(Gp, stem: Path):
    ox.save_graphml(Gp, filepath=str(stem.with_suffix(".graphml")))
    try:
        ox.save_graph_geopackage(Gp, filepath=str(stem.with_suffix(".gpkg")))
    except Exception as exc:  # noqa: BLE001
        print(f"  ⚠  GeoPackage save failed ({exc}); GraphML written.",
              file=sys.stderr)


def _json_default(o):
    """Coerce numpy scalars (osmnx node ids etc.) to plain Python."""
    if hasattr(o, "item"):
        return o.item()
    return str(o)


def write_report(stem, report):
    stem.with_suffix(".report.json").write_text(
        json.dumps(report, indent=2, default=_json_default))

    lines = []
    b = report["boundary"]
    lines.append(f"Traceable reference report — {b['name']}")
    lines.append("=" * 60)
    lines.append(f"OSM id           : {b['osmid']}")
    lines.append(f"Area             : {b['area_acres']:,.0f} acres")
    lines.append("")
    c = report["counts"]
    lines.append(f"Nodes            : {c['nodes']}")
    lines.append(f"Edges            : {c['edges']}")
    lines.append(f"  roads          : {c['road']}")
    lines.append(f"  trails         : {c['trail']}")
    lines.append(f"  unknown        : {c['unknown']}")
    ratio = (c["road"] / c["trail"]) if c["trail"] else float("inf")
    lines.append(f"  road:trail     : {ratio:.2f}")
    lines.append(f"  golf cart paths: {c['cart_paths']}  "
                 "(use --drop-cart-paths to filter)")
    lines.append(f"POIs (kept)      : {c['pois']}")
    lines.append(f"Buildings        : {c.get('buildings', 0)}")
    lines.append(f"Water bodies     : {c.get('water_bodies', 0)}")
    lines.append("")
    lines.append(f"Bridges          : {report['topology']['bridge_count']}")
    lines.append("Articulation pts : "
                 f"{report['topology']['articulation_points']}")
    lines.append(f"Entrances        : {len(report['entrances'])}")
    lrp = report["longest_road_path"]
    if lrp:
        lines.append(f"Longest road span: {lrp['length_mi']} mi "
                     f"({lrp['length_m']} m)")
    lines.append("")
    if report["unknown_highways"]:
        lines.append("Unclassified highway= values (DECIDE these):")
        for h, n in sorted(report["unknown_highways"].items(),
                           key=lambda kv: -kv[1]):
            lines.append(f"  {h:<20} x{n}")
        lines.append("")
    lines.append("Chokepoints (bridges first, then high betweenness):")
    for ch in report["topology"]["chokepoints"][:40]:
        tag = "BRIDGE" if ch["bridge"] else "high-btw"
        nm = ch["name"] or "(unnamed)"
        lines.append(f"  [{tag:<8}] {ch['kind']:<7} {nm}  "
                     f"btw={ch['betweenness']}")
    lines.append("")
    lines.append("Entrances (road crossings of the park boundary):")
    for e in report["entrances"]:
        lines.append(f"  node {e['node']}  {e['kind']}  "
                     f"{e['name'] or '(unnamed)'}")

    stem.with_suffix(".report.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


# --------------------------------------------------------------------------- #
# Driver                                                                       #
# --------------------------------------------------------------------------- #

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--park", default=DEFAULT_PARK,
                    help="Place name to geocode (default: Hard Labor Creek).")
    ap.add_argument("--osmid",
                    help="OSM id for the park relation, e.g. 'R1234567'. "
                         "More reliable than the name.")
    ap.add_argument("--out", default="out/hard_labor_creek",
                    help="Output path stem; siblings .pdf/.graphml/.gpkg/"
                         ".report.* are written next to it.")
    ap.add_argument("--orientation", choices=["auto", "portrait", "landscape"],
                    default="auto")
    ap.add_argument("--consolidate-tolerance", type=float, default=12.0,
                    help="Metres for junction consolidation (0 disables).")
    ap.add_argument("--min-poi-sep-in", type=float, default=0.16,
                    help="Min POI separation on paper, inches (token size).")
    ap.add_argument("--margin-in", type=float, default=0.15,
                    help="Paper margin in inches; smaller = larger drawing. "
                         "Most home printers can't print past ~0.15in.")
    ap.add_argument("--buildings", action="store_true",
                    help="Fetch/draw building footprints (off by default -- "
                         "they add little worth tracing).")
    ap.add_argument("--labels", action="store_true",
                    help="Draw POI / water / trail name labels (off by "
                         "default -- they crowd the linework when tracing).")
    ap.add_argument("--drop-cart-paths", action="store_true",
                    help="Remove edges flagged as golf cart paths.")
    ap.add_argument("--allow-any", action="store_true",
                    help="Skip the 'is this really the park?' guard.")
    args = ap.parse_args(argv)

    ox.settings.log_console = False
    ox.settings.use_cache = True

    stem = Path(args.out)
    stem.parent.mkdir(parents=True, exist_ok=True)

    # 1. boundary
    geom4326, name, area_acres, osmid_str = fetch_boundary(
        args.park, args.osmid, args.allow_any)

    # 2-3. network
    print("\n── Network ──────────────────────────────────────────────")
    G = pull_network(geom4326)
    print(f"  raw graph: {G.number_of_nodes()} nodes, "
          f"{G.number_of_edges()} edges")

    # 5. project + consolidate
    Gp = project_and_consolidate(G, args.consolidate_tolerance)
    crs = Gp.graph["crs"]
    counts, unknown_types, cart_paths = annotate_edges(Gp)

    if args.drop_cart_paths:
        drop = [(u, v, k) for u, v, k, d in Gp.edges(keys=True, data=True)
                if d.get("cart_path")]
        Gp.remove_edges_from(drop)
        Gp.remove_nodes_from(list(nx.isolates(Gp)))
        counts, unknown_types, cart_paths_after = annotate_edges(Gp)
        print(f"  dropped {len(drop)} cart-path edges")

    print(f"  final graph: {Gp.number_of_nodes()} nodes, "
          f"{Gp.number_of_edges()} edges "
          f"(road {counts['road']} / trail {counts['trail']} / "
          f"unknown {counts['unknown']})")

    # project boundary into graph CRS
    import geopandas as gpd
    boundary_proj = gpd.GeoSeries([geom4326], crs="EPSG:4326").to_crs(crs).iloc[0]
    boundary_proj = unary_union(boundary_proj)

    # 6. topology
    print("\n── Topology ─────────────────────────────────────────────")
    topo = analyze_topology(Gp)
    entrances = find_entrances(Gp, boundary_proj)
    lrp = longest_road_path(Gp, topo["_UG"])
    del topo["_UG"]
    print(f"  bridges: {topo['bridge_count']}, "
          f"articulation pts: {topo['articulation_points']}, "
          f"entrances: {len(entrances)}")

    # 4. POIs (min separation derived from paper scale)
    print("\n── POIs ─────────────────────────────────────────────────")
    b = boundary_proj.bounds
    span_m = max(b[2] - b[0], b[3] - b[1])
    fig_w, fig_h = choose_orientation(b, args.orientation)
    meters_per_inch = span_m / (max(fig_w, fig_h) - 2 * args.margin_in)
    min_sep_m = args.min_poi_sep_in * meters_per_inch
    pois_raw = pull_pois(geom4326, crs)
    pois = dedupe_pois(pois_raw, min_sep_m)
    print(f"  {len(pois_raw)} candidates -> {len(pois)} after overlap cull "
          f"(min sep {min_sep_m:.0f} m)")
    counts["pois"] = len(pois)

    # water bodies (shaded) + creeks (lines) + buildings (footprints) to trace
    water = pull_water(geom4326, crs)
    waterways = pull_waterways(geom4326, crs)
    buildings = pull_buildings(geom4326, crs) if args.buildings else []
    print(f"  water: {len(water)} bodies, {len(waterways)} waterways, "
          f"buildings: {len(buildings)} footprints")

    counts["nodes"] = Gp.number_of_nodes()
    counts["edges"] = Gp.number_of_edges()
    counts["cart_paths"] = cart_paths
    counts["buildings"] = len(buildings)
    counts["water_bodies"] = len(water)
    counts["waterways"] = len(waterways)

    # 7. render
    print("\n── Render ───────────────────────────────────────────────")
    out_pdf = stem.with_suffix(".pdf")
    render_pdf(Gp, boundary_proj, pois, water, waterways, buildings, name,
               out_pdf, args.orientation, args.margin_in, args.labels)
    print(f"  wrote {out_pdf}")

    # 8. save graph + report
    save_graph(Gp, stem)
    report = {
        "boundary": {"name": name, "osmid": osmid_str,
                     "area_acres": area_acres},
        "counts": counts,
        "unknown_highways": unknown_types,
        "topology": topo,
        "entrances": entrances,
        "longest_road_path": lrp,
    }
    print("\n── Report ───────────────────────────────────────────────")
    write_report(stem, report)
    print(f"\n✔ Done. Print {out_pdf} on US Letter and trace.")


if __name__ == "__main__":
    main()
