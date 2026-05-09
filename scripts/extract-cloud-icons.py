#!/usr/bin/env python3
"""
extract-cloud-icons.py
----------------------
Extract official cloud provider icon data from the draw.io shape search index.

IMPORTANT: GCP and AWS use DIFFERENT icon storage formats:
  - GCP: Icons are embedded as base64 SVG data URIs (data:image/svg+xml,BASE64)
         → Output: { "Kubernetes Engine": "data:image/svg+xml,PHN2ZyB..." }
  - AWS: Icons are draw.io native shape names (shape=mxgraph.aws4.xxx)
         → Output: { "EC2": "outlineConnect=0;...shape=mxgraph.aws4.ec2;..." }
  - Azure: Similar to AWS, uses mxgraph.azure shape names

Use --mode=svg for GCP, --mode=style for AWS/Azure (auto-detected if not specified).

Usage:
    # GCP (auto-detects SVG mode)
    python3 extract-cloud-icons.py --provider gcp --keywords "Kubernetes Engine" "Cloud IAM"
    python3 extract-cloud-icons.py --provider gcp --all --output gcp_icons.json

    # AWS (auto-detects style mode)
    python3 extract-cloud-icons.py --provider aws --keywords "EC2" "Elastic Kubernetes Service" "Application Load Balancer"
    python3 extract-cloud-icons.py --provider aws --all --output aws_styles.json

    python3 extract-cloud-icons.py --list-providers

Output JSON:
    { "ServiceTitle": "<value>" }
    For GCP: value = "data:image/svg+xml,BASE64..."
    For AWS: value = "outlineConnect=0;...shape=mxgraph.aws4.xxx;..."
"""

import argparse
import json
import re
import sys

INDEX_PATH = "/Users/awawa/.gemini/antigravity/skills/drawio/scripts/shape-search/search-index.json"

PROVIDER_FILTERS = {
    "gcp": ["gcp", "google cloud", "mxgraph.gcp"],
    "aws": ["aws4", "aws3", "amazon", "mxgraph.aws"],
    "azure": ["azure", "microsoft azure", "mxgraph.azure"],
}

# GCP stores icons as base64 SVG in style; AWS/Azure use shape names
SVG_PROVIDERS = {"gcp"}
STYLE_PROVIDERS = {"aws", "azure"}


def load_index(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_provider_item(item, provider):
    """Check if an item belongs to a given cloud provider."""
    filters = PROVIDER_FILTERS.get(provider.lower(), [provider.lower()])
    tags = item.get("tags", "").lower()
    style = item.get("style", "").lower()
    title = item.get("title", "").lower()
    return any(f in tags or f in style or f in title for f in filters)


def extract_svg(style):
    """Extract base64 SVG data URI from a draw.io style string (GCP only)."""
    match = re.search(r"image=(data:image/svg\+xml,[A-Za-z0-9+/=]+)", style)
    return match.group(1) if match else None


def extract_style(style, provider):
    """Extract the full style string for native shape icons (AWS/Azure)."""
    # Prefer aws4 shapes over aws3 for modern icons
    prov = provider.lower()
    if prov == "aws":
        if "mxgraph.aws4" in style or "mxgraph.aws3" in style:
            return style
    elif prov == "azure":
        if "mxgraph.azure" in style or "mxgraph.mscae" in style:
            return style
    return style if style.strip() else None


def get_icon_value(item, provider, mode):
    """Extract the icon value (SVG or style string) based on mode."""
    style = item.get("style", "")
    if mode == "svg":
        return extract_svg(style)
    else:
        return extract_style(style, provider) if style.strip() else None


def find_icons(data, provider, keywords, mode):
    """Find icons matching keywords for a given provider."""
    results = {}
    kw_lower = [k.lower() for k in keywords]
    for item in data:
        if not is_provider_item(item, provider):
            continue
        title = item.get("title", "")
        for kw in kw_lower:
            if kw in title.lower() and kw not in results:
                value = get_icon_value(item, provider, mode)
                if value:
                    results[kw] = {"title": title, "value": value}
                    break
    return results


def find_all_icons(data, provider, mode):
    """Extract all icons for a given provider."""
    results = {}
    # For AWS, prefer aws4 entries
    prefer_v4 = provider.lower() == "aws"
    first_pass = {}

    for item in data:
        if not is_provider_item(item, provider):
            continue
        title = item.get("title", "")
        tags = item.get("tags", "").lower()
        if not title:
            continue
        value = get_icon_value(item, provider, mode)
        if value:
            if title not in first_pass:
                first_pass[title] = (value, "aws4" in tags)
            elif prefer_v4 and "aws4" in tags and not first_pass[title][1]:
                first_pass[title] = (value, True)

    return {title: val for title, (val, _) in first_pass.items()}


def detect_mode(provider):
    """Auto-detect extraction mode based on provider."""
    if provider.lower() in SVG_PROVIDERS:
        return "svg"
    return "style"


def list_providers():
    print("Supported providers and their icon modes:")
    print("  gcp   -> mode=svg   (base64 SVG data URIs, used with card_node() in build-cloud-diagram.py)")
    print("  aws   -> mode=style (mxgraph.aws4 shape styles, used with icon_node())")
    print("  azure -> mode=style (mxgraph.azure shape styles, used with icon_node())")


def main():
    parser = argparse.ArgumentParser(
        description="Extract cloud provider icon data from draw.io search index."
    )
    parser.add_argument("--provider", "-p", default="gcp",
                        help="Cloud provider: gcp, aws, azure")
    parser.add_argument("--keywords", "-k", nargs="+",
                        help="Service name keywords to search for (partial match)")
    parser.add_argument("--all", "-a", action="store_true",
                        help="Extract all icons for the provider")
    parser.add_argument("--mode", choices=["svg", "style"],
                        help="Override extraction mode (default: auto-detect from provider)")
    parser.add_argument("--list-providers", action="store_true",
                        help="List available providers and their modes")
    parser.add_argument("--index", default=INDEX_PATH,
                        help="Path to search-index.json")
    parser.add_argument("--output", "-o",
                        help="Output JSON file path (default: stdout)")
    args = parser.parse_args()

    if args.list_providers:
        list_providers()
        return

    if not args.keywords and not args.all:
        print("Error: specify --keywords or --all", file=sys.stderr)
        sys.exit(1)

    mode = args.mode or detect_mode(args.provider)
    print(f"Provider: {args.provider} | Mode: {mode}", file=sys.stderr)

    data = load_index(args.index)

    if args.all:
        results = find_all_icons(data, args.provider, mode)
        print(f"Found {len(results)} icons", file=sys.stderr)
    else:
        raw = find_icons(data, args.provider, args.keywords, mode)
        results = {v["title"]: v["value"] for v in raw.values()}
        found_kws = set()
        for kw in args.keywords:
            if any(kw.lower() in t.lower() for t in results):
                found_kws.add(kw)
        missing = [k for k in args.keywords if k not in found_kws]
        if missing:
            print(f"WARNING: No icon found for: {missing}", file=sys.stderr)
            print("Tip: Run --all to list all available titles, then use exact names.", file=sys.stderr)

    output_json = json.dumps(results, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"Saved {len(results)} icons to {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
