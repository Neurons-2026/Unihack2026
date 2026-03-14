"""
Generate a standalone HTML visualization from any knowledge graph JSON file.

Usage:
    python -m test_graph_building.generate_viz path/to/knowledge_graph.json
    python -m test_graph_building.generate_viz path/to/knowledge_graph.json -o output.html
    python -m test_graph_building.generate_viz path/to/knowledge_graph.json --title "My Graph"
"""

import argparse
import json
import sys
from pathlib import Path


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{{TITLE}}</title>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
      background: #0f1117;
      color: #e0e0e0;
      overflow: hidden;
    }
    #graph-container {
      width: 100vw;
      height: 100vh;
      position: relative;
    }
    svg { display: block; }

    /* Tooltip */
    #tooltip {
      position: absolute;
      pointer-events: none;
      background: rgba(20, 22, 30, 0.95);
      border: 1px solid rgba(100, 120, 255, 0.3);
      border-radius: 10px;
      padding: 14px 18px;
      max-width: 380px;
      font-size: 13px;
      line-height: 1.5;
      box-shadow: 0 8px 32px rgba(0,0,0,0.5);
      display: none;
      z-index: 100;
      backdrop-filter: blur(8px);
    }
    #tooltip .tt-label {
      font-size: 15px;
      font-weight: 700;
      color: #fff;
      margin-bottom: 6px;
    }
    #tooltip .tt-source {
      font-size: 11px;
      color: #888;
      margin-bottom: 8px;
    }
    #tooltip .tt-cat {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      margin-bottom: 8px;
    }
    #tooltip .tt-section {
      margin-top: 8px;
    }
    #tooltip .tt-section-title {
      font-size: 11px;
      font-weight: 600;
      color: #aaa;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 2px;
    }
    #tooltip .tt-edge-info {
      font-size: 12px;
      color: #7eb8ff;
      margin-top: 6px;
    }

    /* Legend */
    #legend {
      position: absolute;
      top: 16px;
      left: 16px;
      background: rgba(20, 22, 30, 0.9);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 10px;
      padding: 14px 18px;
      font-size: 12px;
      z-index: 50;
    }
    #legend h3 {
      font-size: 14px;
      margin-bottom: 10px;
      color: #fff;
    }
    .legend-item {
      display: flex;
      align-items: center;
      margin-bottom: 5px;
    }
    .legend-dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      margin-right: 8px;
      flex-shrink: 0;
    }

    /* Source legend */
    #source-legend {
      position: absolute;
      top: 16px;
      left: 180px;
      background: rgba(20, 22, 30, 0.9);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 10px;
      padding: 14px 18px;
      font-size: 12px;
      z-index: 50;
      max-width: 380px;
    }
    #source-legend h3 {
      font-size: 14px;
      margin-bottom: 10px;
      color: #fff;
    }
    .source-item {
      display: flex;
      align-items: flex-start;
      margin-bottom: 6px;
    }
    .source-ring {
      width: 14px;
      height: 14px;
      border-radius: 50%;
      margin-right: 8px;
      flex-shrink: 0;
      margin-top: 1px;
      border: 3px solid;
      background: transparent;
    }
    .source-item span {
      font-size: 11px;
      line-height: 1.4;
    }

    /* Controls */
    #controls {
      position: absolute;
      top: 16px;
      right: 16px;
      background: rgba(20, 22, 30, 0.9);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 10px;
      padding: 14px 18px;
      font-size: 12px;
      z-index: 50;
      min-width: 220px;
    }
    #controls h3 {
      font-size: 14px;
      margin-bottom: 10px;
      color: #fff;
    }
    #controls label {
      display: block;
      margin-bottom: 4px;
      color: #aaa;
    }
    #controls input[type="range"] {
      width: 100%;
      margin-bottom: 10px;
    }
    #threshold-val {
      color: #7eb8ff;
      font-weight: 600;
    }

    /* Title bar */
    #title-bar {
      position: absolute;
      bottom: 16px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(20, 22, 30, 0.9);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 10px;
      padding: 10px 24px;
      font-size: 13px;
      color: #aaa;
      z-index: 50;
      text-align: center;
    }
    #title-bar strong { color: #fff; }
  </style>
</head>
<body>
  <div id="graph-container">
    <svg id="graph-svg"></svg>

    <div id="legend">
      <h3>Categories</h3>
    </div>

    <div id="source-legend">
      <h3>Sources (ring color)</h3>
    </div>

    <div id="controls">
      <h3>Controls</h3>
      <label>Similarity threshold: <span id="threshold-val">{{THRESHOLD}}</span></label>
      <input type="range" id="threshold-slider" min="0.1" max="0.9" step="0.01" value="{{THRESHOLD}}" />
      <label style="margin-top: 6px;">
        <input type="checkbox" id="show-labels" checked /> Show labels
      </label>
    </div>

    <div id="title-bar">
      <strong>{{TITLE}}</strong> &mdash; {{SUMMARY}}
    </div>

    <div id="tooltip"></div>
  </div>

  <script>
    const CATEGORY_COLORS = {
      technique: "#6C8EFF",
      architecture: "#FF6C8E",
      application: "#6CFF8E",
      dataset: "#FFD56C",
      tool: "#C86CFF",
      benchmark: "#FF8E6C",
      theory: "#6CFFD5",
    };

    // Auto-generated source color palette
    const SOURCE_PALETTE = [
      "#FF9E44", "#44D4FF", "#FF44A1", "#44FF8E", "#D4A0FF",
      "#FFD644", "#44FFD4", "#FF6E44", "#44A1FF", "#A1FF44",
      "#FF44D4", "#8EFF44", "#4468FF", "#FF4444", "#44FFA1",
    ];

    const graphData = {{GRAPH_DATA}};

    // Build source color map dynamically
    const allSources = [...new Set(graphData.nodes.map(n => n.source_file))].sort();
    const SOURCE_COLORS = {};
    allSources.forEach((src, i) => {
      SOURCE_COLORS[src] = SOURCE_PALETTE[i % SOURCE_PALETTE.length];
    });

    const width = window.innerWidth;
    const height = window.innerHeight;

    const svg = d3.select("#graph-svg")
      .attr("width", width)
      .attr("height", height);

    // Defs for glow effect
    const defs = svg.append("defs");
    const filter = defs.append("filter").attr("id", "glow");
    filter.append("feGaussianBlur").attr("stdDeviation", "3").attr("result", "coloredBlur");
    const feMerge = filter.append("feMerge");
    feMerge.append("feMergeNode").attr("in", "coloredBlur");
    feMerge.append("feMergeNode").attr("in", "SourceGraphic");

    const container = svg.append("g");

    // Zoom
    const zoom = d3.zoom()
      .scaleExtent([0.1, 8])
      .on("zoom", (event) => container.attr("transform", event.transform));
    svg.call(zoom);

    const tooltip = d3.select("#tooltip");

    let currentThreshold = {{THRESHOLD}};

    // Build legends
    buildLegend(graphData.nodes);
    buildSourceLegend(graphData.nodes);
    render(graphData, currentThreshold);

    function buildLegend(nodes) {
      const categories = [...new Set(nodes.map(n => n.category))].sort();
      const legend = d3.select("#legend");
      categories.forEach(cat => {
        const item = legend.append("div").attr("class", "legend-item");
        item.append("div")
          .attr("class", "legend-dot")
          .style("background", CATEGORY_COLORS[cat] || "#888");
        item.append("span").text(cat);
      });
    }

    function buildSourceLegend(nodes) {
      const sources = [...new Set(nodes.map(n => n.source_file))];
      const legend = d3.select("#source-legend");
      if (sources.length <= 1) {
        legend.style("display", "none");
        return;
      }
      sources.forEach(src => {
        const title = nodes.find(n => n.source_file === src)?.source_title || src;
        const color = SOURCE_COLORS[src] || "#888";
        const item = legend.append("div").attr("class", "source-item");
        item.append("div")
          .attr("class", "source-ring")
          .style("border-color", color);
        item.append("span").html(`<strong>${src}</strong><br/>${title}`);
      });
    }

    function render(data, threshold) {
      container.selectAll("*").remove();

      const nodes = data.nodes.map(d => ({ ...d }));
      const links = data.links
        .filter(l => l.similarity >= threshold)
        .map(l => ({
          source: l.source,
          target: l.target,
          weight: l.weight,
          similarity: l.similarity,
        }));

      const maxSim = d3.max(links, d => d.similarity) || 1;
      const minSim = d3.min(links, d => d.similarity) || 0;

      // Scale forces based on node count
      const n = nodes.length;
      const chargeStrength = n > 40 ? -200 : n > 20 ? -300 : -350;
      const collisionRadius = n > 40 ? 30 : n > 20 ? 38 : 45;

      const simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(d => d.id).distance(d => 180 - d.similarity * 100))
        .force("charge", d3.forceManyBody().strength(chargeStrength))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collision", d3.forceCollide().radius(collisionRadius));

      // Draw edges
      const link = container.append("g")
        .selectAll("line")
        .data(links)
        .join("line")
        .attr("stroke", d => {
          const t = minSim === maxSim ? 1 : (d.similarity - minSim) / (maxSim - minSim);
          return d3.interpolateRgb("#2a3a5c", "#6C8EFF")(t);
        })
        .attr("stroke-opacity", d => 0.3 + 0.5 * d.similarity)
        .attr("stroke-width", d => 1 + 3 * d.similarity);

      // Draw nodes
      const node = container.append("g")
        .selectAll("g")
        .data(nodes)
        .join("g")
        .call(d3.drag()
          .on("start", dragstarted)
          .on("drag", dragged)
          .on("end", dragended));

      const hasManySource = allSources.length > 1;

      // Node circle
      node.append("circle")
        .attr("r", d => 8 + (d.relevance_score || 0.5) * 12)
        .attr("fill", d => CATEGORY_COLORS[d.category] || "#888")
        .attr("stroke", d => hasManySource ? (SOURCE_COLORS[d.source_file] || "#888") : "#fff")
        .attr("stroke-width", hasManySource ? 3 : 1.5)
        .attr("opacity", 0.9)
        .style("filter", "url(#glow)");

      // Node labels
      const labels = node.append("text")
        .text(d => d.label)
        .attr("dx", d => 12 + (d.relevance_score || 0.5) * 8)
        .attr("dy", 4)
        .attr("font-size", n > 40 ? "10px" : "11px")
        .attr("fill", "#ccc")
        .attr("font-weight", 500)
        .attr("class", "node-label");

      // Hover interactions — nodes
      node.on("mouseover", function(event, d) {
        link.attr("stroke-opacity", l =>
          (l.source.id === d.id || l.target.id === d.id) ? 1 : 0.08
        ).attr("stroke-width", l =>
          (l.source.id === d.id || l.target.id === d.id) ? 3 + 3 * l.similarity : 1
        );

        const connected = new Set();
        connected.add(d.id);
        links.forEach(l => {
          const sid = typeof l.source === "object" ? l.source.id : l.source;
          const tid = typeof l.target === "object" ? l.target.id : l.target;
          if (sid === d.id) connected.add(tid);
          if (tid === d.id) connected.add(sid);
        });
        node.select("circle").attr("opacity", n => connected.has(n.id) ? 1 : 0.15);
        node.select("text").attr("opacity", n => connected.has(n.id) ? 1 : 0.15);

        const connEdges = links.filter(l => {
          const sid = typeof l.source === "object" ? l.source.id : l.source;
          const tid = typeof l.target === "object" ? l.target.id : l.target;
          return sid === d.id || tid === d.id;
        });

        const catColor = CATEGORY_COLORS[d.category] || "#888";
        let html = `
          <div class="tt-label">${d.label}</div>
          <div class="tt-source">${d.source_title || d.source_file || ""}</div>
          <span class="tt-cat" style="background:${catColor}33;color:${catColor}">${d.category}</span>
          <span style="margin-left:6px;font-size:11px;color:#aaa;">relevance: ${d.relevance_score}</span>`;

        if (d.description) {
          html += `<div class="tt-section">
            <div class="tt-section-title">Description</div>
            ${d.description}
          </div>`;
        }
        if (d.why_innovative) {
          html += `<div class="tt-section">
            <div class="tt-section-title">Why Innovative</div>
            ${d.why_innovative}
          </div>`;
        }
        if (d.impact_on_applications) {
          html += `<div class="tt-section">
            <div class="tt-section-title">Impact on Applications</div>
            ${d.impact_on_applications}
          </div>`;
        }
        if (connEdges.length > 0) {
          html += `<div class="tt-edge-info">${connEdges.length} connection(s)</div>`;
        }

        tooltip.html(html).style("display", "block");
        moveTooltip(event);
      })
      .on("mousemove", moveTooltip)
      .on("mouseout", function() {
        link.attr("stroke-opacity", d => 0.3 + 0.5 * d.similarity)
            .attr("stroke-width", d => 1 + 3 * d.similarity);
        node.select("circle").attr("opacity", 0.9);
        node.select("text").attr("opacity", 1);
        tooltip.style("display", "none");
      });

      // Edge hover
      link.on("mouseover", function(event, d) {
        const srcLabel = typeof d.source === "object" ? d.source.label : d.source;
        const tgtLabel = typeof d.target === "object" ? d.target.label : d.target;
        tooltip.html(`
          <div class="tt-label">${srcLabel} &harr; ${tgtLabel}</div>
          <div class="tt-edge-info">Cosine similarity: <strong>${d.similarity.toFixed(4)}</strong></div>
        `).style("display", "block");
        moveTooltip(event);
        d3.select(this).attr("stroke", "#fff").attr("stroke-opacity", 1);
      })
      .on("mousemove", moveTooltip)
      .on("mouseout", function(event, d) {
        tooltip.style("display", "none");
        const t = minSim === maxSim ? 1 : (d.similarity - minSim) / (maxSim - minSim);
        d3.select(this)
          .attr("stroke", d3.interpolateRgb("#2a3a5c", "#6C8EFF")(t))
          .attr("stroke-opacity", 0.3 + 0.5 * d.similarity);
      });

      simulation.on("tick", () => {
        link
          .attr("x1", d => d.source.x)
          .attr("y1", d => d.source.y)
          .attr("x2", d => d.target.x)
          .attr("y2", d => d.target.y);
        node.attr("transform", d => `translate(${d.x},${d.y})`);
      });

      // Toggle labels
      d3.select("#show-labels").on("change", function() {
        labels.style("display", this.checked ? "block" : "none");
      });

      function dragstarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
      }
      function dragged(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
      }
      function dragended(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
      }
    }

    function moveTooltip(event) {
      let x = event.pageX + 15;
      let y = event.pageY + 15;
      const ttNode = tooltip.node();
      const rect = ttNode.getBoundingClientRect();
      if (x + rect.width > window.innerWidth - 10) x = event.pageX - rect.width - 15;
      if (y + rect.height > window.innerHeight - 10) y = event.pageY - rect.height - 15;
      tooltip.style("left", x + "px").style("top", y + "px");
    }

    // Threshold slider
    d3.select("#threshold-slider").on("input", function() {
      currentThreshold = +this.value;
      d3.select("#threshold-val").text(currentThreshold.toFixed(2));
      render(graphData, currentThreshold);
    });

    // Resize
    window.addEventListener("resize", () => {
      svg.attr("width", window.innerWidth).attr("height", window.innerHeight);
    });
  </script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(
        description="Generate a standalone HTML visualization from a knowledge graph JSON file"
    )
    parser.add_argument(
        "input",
        help="Path to the knowledge graph JSON file (node-link format)",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output HTML file path (default: same directory as input, named visualize.html)",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Title for the visualization (default: auto-generated from filename)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Initial similarity threshold (default: auto from data)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        graph_data = json.load(f)

    # Validate structure
    if "nodes" not in graph_data or "links" not in graph_data:
        print("Error: JSON must have 'nodes' and 'links' keys (node-link format)", file=sys.stderr)
        sys.exit(1)

    n_nodes = len(graph_data["nodes"])
    n_edges = len(graph_data["links"])
    sources = set(n.get("source_file", "") for n in graph_data["nodes"])
    sources.discard("")

    # Auto-detect threshold from data
    if args.threshold is not None:
        threshold = args.threshold
    elif n_edges > 0:
        sims = [l.get("similarity", l.get("weight", 0)) for l in graph_data["links"]]
        threshold = round(min(sims), 2)
    else:
        threshold = 0.4

    # Title
    title = args.title or f"Knowledge Graph — {input_path.stem}"

    # Summary line
    source_str = f" from {len(sources)} source(s)" if sources else ""
    summary = f"{n_nodes} concepts{source_str}, {n_edges} edges, threshold {threshold:.2f}"

    # Output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.parent / "visualize.html"

    # Build HTML
    graph_json = json.dumps(graph_data, ensure_ascii=False)
    html = HTML_TEMPLATE
    html = html.replace("{{TITLE}}", title)
    html = html.replace("{{SUMMARY}}", summary)
    html = html.replace("{{THRESHOLD}}", f"{threshold:.2f}")
    html = html.replace("{{GRAPH_DATA}}", graph_json)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Generated: {output_path}")
    print(f"  Nodes: {n_nodes}, Edges: {n_edges}, Threshold: {threshold:.2f}")
    print(f"  Sources: {sorted(sources) if sources else ['(none)']}")


if __name__ == "__main__":
    main()
