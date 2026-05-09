#!/usr/bin/env python3
"""
build-cloud-diagram.py
-----------------------
Generate a draw.io XML file with official cloud provider component icons.

Supports two rendering approaches based on provider:

  GCP  → gcp_icon_node(): single image cell with embedded base64 SVG icon
  AWS  → icon_node()    : native mxgraph.aws4 shape (direct style string)
  Azure→ icon_node()    : native mxgraph.azure shape (direct style string)

Icon data comes from extract-cloud-icons.py output JSON.

Usage (GCP):
    python3 extract-cloud-icons.py --provider gcp --keywords "GKE" "Cloud IAM" -o /tmp/gcp.json
    python3 build-cloud-diagram.py --provider gcp --icons /tmp/gcp.json --output diagram.drawio

Usage (AWS):
    python3 extract-cloud-icons.py --provider aws --keywords "EC2" "Application Load Balancer" -o /tmp/aws.json
    python3 build-cloud-diagram.py --provider aws --icons /tmp/aws.json --output diagram.drawio
"""

import argparse
import json
import sys


# ---------------------------------------------------------------------------
# GCP: gcp_icon_node (single image cell + embedded SVG)
# Use when icons JSON contains "data:image/svg+xml,BASE64" values
# ---------------------------------------------------------------------------

def gcp_icon_node(node_id, label, svg, x, y, parent="1", width=40, height=40):
    """
    Official GCP icon style: shape=image with embedded base64 SVG icon.
    svg: "data:image/svg+xml,BASE64..." from extract-cloud-icons.py --provider gcp
    """
    img_attr = "image=" + svg + ";" if svg else "image=;"
    lbl = _esc(label)
    return (
        '<mxCell id="' + node_id + '" parent="' + parent + '" '
        'style="shape=image;html=1;labelPosition=bottom;'
        'verticalLabelPosition=top;align=center;verticalAlign=bottom;'
        'fontSize=10;fontStyle=1;' + img_attr + '" '
        'value="' + lbl + '" vertex="1">\n'
        '  <mxGeometry height="' + str(height) + '" width="' + str(width) + '" '
        'x="' + str(x) + '" y="' + str(y) + '" as="geometry" />\n'
        '</mxCell>'
    )


# ---------------------------------------------------------------------------
# AWS / Azure: icon_node (native mxgraph shape style)
# Use when icons JSON contains full style strings like "outlineConnect=0;...shape=mxgraph.aws4.ec2;..."
# ---------------------------------------------------------------------------

def icon_node(node_id, label, style, x, y, parent="1", width=78, height=78):
    """
    Native AWS/Azure icon: single mxCell using the full style string from search-index.json.
    style: full draw.io style string from extract-cloud-icons.py --provider aws
    Label appears below the icon (verticalLabelPosition=bottom is already in style).
    """
    lbl = _esc(label)
    return (
        '<mxCell id="' + node_id + '" parent="' + parent + '" value="' + lbl + '" '
        'style="' + style + '" vertex="1">\n'
        '  <mxGeometry x="' + str(x) + '" y="' + str(y) + '" '
        'width="' + str(width) + '" height="' + str(height) + '" as="geometry" />\n'
        '</mxCell>'
    )


# ---------------------------------------------------------------------------
# Containers
# ---------------------------------------------------------------------------

def gcp_project_container(container_id, label, x, y, width=900, height=560):
    """GCP project boundary (blue dashed swimlane)."""
    lbl = _esc(label)
    return (
        '<mxCell id="' + container_id + '" parent="1" '
        'style="swimlane;dashed=1;startSize=24;fillColor=#f8f9fa;'
        'strokeColor=#4285F4;html=1;fontColor=#4285F4;fontStyle=1;" '
        'value="' + lbl + '" vertex="1">\n'
        '  <mxGeometry height="' + str(height) + '" width="' + str(width) + '" '
        'x="' + str(x) + '" y="' + str(y) + '" as="geometry" />\n'
        '</mxCell>'
    )


def aws_vpc_container(container_id, label, x, y, width=900, height=220):
    """AWS VPC boundary group (purple aws4 group shape)."""
    lbl = _esc(label)
    return (
        '<mxCell id="' + container_id + '" parent="1" '
        'style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[0,0.25],[0,0.5],[0,0.75],'
        '[0,1],[0.25,1],[0.5,1],[0.75,1],[1,1],[1,0.25],[1,0.5],[1,0.75]];'
        'shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc;grStroke=1;'
        'strokeColor=#8C4FFF;fillColor=#F5F0FF;verticalAlign=top;align=center;'
        'spacingTop=25;fontSize=14;fontStyle=1;fontColor=#8C4FFF;whiteSpace=wrap;html=1;" '
        'value="' + lbl + '" vertex="1">\n'
        '  <mxGeometry height="' + str(height) + '" width="' + str(width) + '" '
        'x="' + str(x) + '" y="' + str(y) + '" as="geometry" />\n'
        '</mxCell>'
    )


# ---------------------------------------------------------------------------
# Edges
# ---------------------------------------------------------------------------

def connector(edge_id, src_id, tgt_id, parent="1", dashed=False, label="",
              provider="gcp"):
    """
    Orthogonal edge between nodes.
    For both GCP and AWS, src/tgt are the node_ids directly.
    """
    stroke = "#4285F4" if provider == "gcp" else "#FF9900"
    dstyle = "dashed=1;" if dashed else ""
    return (
        '<mxCell id="' + edge_id + '" edge="1" parent="' + parent + '" '
        'source="' + src_id + '" target="' + tgt_id + '" '
        'value="' + _esc(label) + '" '
        'style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeWidth=2;'
        'strokeColor=' + stroke + ';' + dstyle + '">\n'
        '  <mxGeometry relative="1" as="geometry"/>\n'
        '</mxCell>'
    )


# ---------------------------------------------------------------------------
# XML wrapper
# ---------------------------------------------------------------------------

def build_xml(cells):
    """Wrap cell fragments into a complete draw.io mxfile XML document."""
    body = "\n".join(
        "        " + line
        for cell in cells
        for line in cell.split("\n")
    )
    return (
        '<mxfile host="draw.io">\n'
        '  <diagram id="cloud_arch" name="Cloud Architecture">\n'
        '    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" '
        'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
        'pageWidth="1169" pageHeight="827" math="0" shadow="0" adaptiveColors="auto">\n'
        '      <root>\n'
        '        <mxCell id="0" />\n'
        '        <mxCell id="1" parent="0" />\n'
        + body + '\n'
        '      </root>\n'
        '    </mxGraphModel>\n'
        '  </diagram>\n'
        '</mxfile>'
    )


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# ---------------------------------------------------------------------------
# Example GCP diagram — customize NODES/EDGES for your project
# ---------------------------------------------------------------------------

GCP_NODES = [
    # (node_id, label,                    icon_title_key,           x,   y,    parent)
    ("user",    "Frontend Client",         "Kubernetes Engine",       40,  300,  "1"),
    ("lb",      "Cloud Load Balancing",    "Cloud Load Balancing",    40,  200,  "gcp"),
    ("gke",     "Kubernetes Engine (GKE)", "Kubernetes Engine",      280,  200,  "gcp"),
    ("gar",     "Artifact Registry",       "Artifact Registry",       280,   40,  "gcp"),
    ("kms",     "Cloud KMS",              "Key Management Service",   560,   40,  "gcp"),
    ("logging", "Cloud Logging",           "Cloud Logging",            560,  200,  "gcp"),
    ("iam",     "Cloud IAM",              "Cloud IAM",                560,  360,  "gcp"),
]

GCP_EDGES = [
    ("e1", "user",  "lb",      "1",   False, ""),
    ("e2", "lb",    "gke",     "gcp", False, ""),
    ("e3", "gke",   "gar",     "gcp", True,  "pull image"),
    ("e4", "gar",   "kms",     "gcp", True,  "encrypt"),
    ("e5", "gke",   "logging", "gcp", True,  "logs"),
    ("e6", "gke",   "iam",     "gcp", True,  "auth"),
]

# ---------------------------------------------------------------------------
# Example AWS diagram
# ---------------------------------------------------------------------------

AWS_NODES = [
    # (node_id, label,                 icon_title_key,               x,   y,    parent, w,  h)
    ("alb",  "Application\nLB",        "Application Load Balancer",   40,  70, "vpc", 78, 78),
    ("sg",   "Security\nGroup",        "Security group",             260,  45, "vpc", 130, 130),
    ("ec2",  "EC2\nInstance",          "EC2",                        500,  70, "vpc",  78,  78),
    ("eks",  "EKS\nCluster",           "Elastic Kubernetes Service",  730,  70, "vpc",  78,  78),
]

AWS_EDGES = [
    ("e1", "alb", "sg",  "vpc", False, "traffic"),
    ("e2", "sg",  "ec2", "vpc", False, "filtered"),
    ("e3", "ec2", "eks", "vpc", False, "orchestrates"),
]


def main():
    parser = argparse.ArgumentParser(description="Build draw.io cloud architecture diagram.")
    parser.add_argument("--provider", "-p", default="gcp", choices=["gcp", "aws", "azure"],
                        help="Cloud provider (affects node/edge style)")
    parser.add_argument("--icons", "-i", required=True,
                        help="JSON file from extract-cloud-icons.py")
    parser.add_argument("--output", "-o", required=True,
                        help="Output .drawio file path")
    parser.add_argument("--project-label", default="Cloud Project",
                        help="Container label (VPC / GCP Project name)")
    args = parser.parse_args()

    with open(args.icons, "r", encoding="utf-8") as f:
        icons = json.load(f)

    cells = []

    if args.provider == "gcp":
        cells.append(gcp_project_container("gcp", args.project_label, 200, 80))
        for node_id, label, key, x, y, parent in GCP_NODES:
            svg = icons.get(key, "")
            if not svg:
                print("WARNING: missing icon for key: " + key, file=sys.stderr)
            cells.append(gcp_icon_node(node_id, label, svg, x, y, parent=parent))
        for eid, src, tgt, parent, dashed, label in GCP_EDGES:
            cells.append(connector(eid, src, tgt, parent=parent, dashed=dashed,
                                   label=label, provider="gcp"))

    elif args.provider == "aws":
        cells.append(aws_vpc_container("vpc", args.project_label, 60, 60))
        for row in AWS_NODES:
            node_id, label, key, x, y, parent = row[:6]
            w = row[6] if len(row) > 6 else 78
            h = row[7] if len(row) > 7 else 78
            style = icons.get(key, "")
            if not style:
                print("WARNING: missing icon for key: " + key, file=sys.stderr)
            cells.append(icon_node(node_id, label, style, x, y, parent=parent, width=w, height=h))
        for eid, src, tgt, parent, dashed, label in AWS_EDGES:
            cells.append(connector(eid, src, tgt, parent=parent, dashed=dashed,
                                   label=label, provider="aws"))

    xml = build_xml(cells)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(xml)
    print("Diagram written to: " + args.output)


if __name__ == "__main__":
    main()
