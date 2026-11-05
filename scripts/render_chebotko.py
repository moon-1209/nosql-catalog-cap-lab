"""Render Chebotko-notation diagrams for Schema A and Schema B as SVG.

Chebotko notation conventions used here:
  * Partition-key columns are marked with a filled key glyph (K).
  * Clustering columns carry an arrow showing clustering order
    (v = DESC, ^ = ASC).
  * Regular (payload) columns sit below the key separator line.
  * Each access pattern is drawn as a labelled arrow into the table
    it is served by.

Run:  python scripts/render_chebotko.py
Out:  docs/schema/chebotko/schema-a.svg, schema-b.svg
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.catalog_analysis.schemas import NUM_BUCKETS

OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "schema" / "chebotko"

FONT = "font-family='Menlo, monospace'"
ROW_H = 22
PAD = 12
TITLE_H = 30


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def table_svg(x, y, w, title, key_cols, payload_cols):
    """key_cols/payload_cols: list of (name, type, marker)."""
    rows = key_cols + payload_cols
    h = TITLE_H + ROW_H * len(rows) + PAD * 2
    out = [
        f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='6' "
        f"fill='#fdfdfd' stroke='#333' stroke-width='1.5'/>",
        f"<rect x='{x}' y='{y}' width='{w}' height='{TITLE_H}' rx='6' "
        f"fill='#dfe9f5' stroke='#333' stroke-width='1.5'/>",
        f"<text x='{x + w / 2}' y='{y + 20}' text-anchor='middle' "
        f"font-size='14' font-weight='bold' {FONT}>{esc(title)}</text>",
    ]
    cy = y + TITLE_H + PAD + 6
    sep_y = y + TITLE_H + PAD + ROW_H * len(key_cols) - 8
    for i, (name, typ, marker) in enumerate(rows):
        if i == len(key_cols):
            out.append(
                f"<line x1='{x}' y1='{sep_y}' x2='{x + w}' y2='{sep_y}' "
                f"stroke='#333' stroke-width='1'/>"
            )
        fill = "#c0392b" if marker.startswith("K") else ("#1a5276" if marker else "#333")
        out.append(
            f"<text x='{x + 10}' y='{cy}' font-size='12' fill='{fill}' {FONT}>"
            f"{esc(name)}</text>"
        )
        out.append(
            f"<text x='{x + w - 10}' y='{cy}' font-size='11' fill='#777' "
            f"text-anchor='end' {FONT}>{esc(typ)}</text>"
        )
        if marker:
            out.append(
                f"<text x='{x + w - 120}' y='{cy}' font-size='12' fill='{fill}' "
                f"font-weight='bold' {FONT}>{esc(marker)}</text>"
            )
        cy += ROW_H
    return "\n".join(out), h


def query_arrow(x1, y1, x2, y2, label="", color="#7d3c98"):
    out = (
        f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' stroke='{color}' "
        f"stroke-width='1.6' marker-end='url(#arr)'/>"
    )
    if label:
        out += (
            f"<text x='{(x1 + x2) / 2}' y='{(y1 + y2) / 2 - 6}' font-size='11' "
            f"fill='{color}' text-anchor='middle' {FONT}>{esc(label)}</text>"
        )
    return out


def legend(x, y):
    items = [
        ("K", "#c0392b", "partition key column"),
        ("C v", "#1a5276", "clustering column, descending"),
        ("C ^", "#1a5276", "clustering column, ascending"),
    ]
    out = [f"<text x='{x}' y='{y}' font-size='12' font-weight='bold' {FONT}>Legend</text>"]
    for i, (mark, color, desc) in enumerate(items):
        yy = y + 18 + i * 18
        out.append(f"<text x='{x}' y='{yy}' font-size='12' fill='{color}' "
                   f"font-weight='bold' {FONT}>{esc(mark)}</text>")
        out.append(f"<text x='{x + 34}' y='{yy}' font-size='12' fill='#333' "
                   f"{FONT}>= {esc(desc)}</text>")
    return "\n".join(out)


def svg(width, height, body):
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' "
        f"height='{height}' viewBox='0 0 {width} {height}'>\n"
        f"<defs><marker id='arr' markerWidth='9' markerHeight='9' refX='7' "
        f"refY='3' orient='auto'><path d='M0,0 L7,3 L0,6 z' fill='#7d3c98'/>"
        f"</marker></defs>\n"
        f"<rect width='{width}' height='{height}' fill='white'/>\n{body}\n</svg>\n"
    )


def schema_a():
    parts = [
        f"<text x='20' y='28' font-size='17' font-weight='bold' {FONT}>"
        f"Schema A - partition per category</text>"
    ]
    tbl, th = table_svg(
        300, 50, 340, "products_by_category",
        [
            ("category_id", "uuid", "K"),
            ("added_at", "timestamp", "C v"),
            ("product_id", "uuid", "C ^"),
        ],
        [
            ("name", "text", ""), ("brand", "text", ""),
            ("price", "decimal", ""), ("currency", "text", ""),
            ("stock", "int", ""), ("rating", "float", ""),
            ("attributes", "map&lt;text,text&gt;", ""),
        ],
    )
    parts.append(tbl)
    tbl2, th2 = table_svg(
        300, 50 + th + 40, 340, "products_by_id",
        [("product_id", "uuid", "K")],
        [("name", "text", ""), ("brand", "text", ""), ("price", "decimal", ""),
         ("currency", "text", ""), ("stock", "int", ""), ("rating", "float", ""),
         ("attributes", "map&lt;text,text&gt;", "")],
    )
    parts.append(tbl2)
    y0 = 90
    for label, ty in [("Q2, Q3, Q4 reads", 150), ("W1, W2, W3 writes", 210)]:
        parts.append(f"<text x='20' y='{y0}' font-size='12' fill='#7d3c98' "
                     f"{FONT}>{label}</text>")
        parts.append(query_arrow(40, y0 + 8, 296, ty))
        y0 += 26
    parts.append(f"<text x='20' y='{50 + th + 110}' font-size='12' "
                 f"fill='#7d3c98' {FONT}>Q1 point lookup</text>")
    parts.append(query_arrow(40, 50 + th + 118, 296, 50 + th + 120))
    parts.append(legend(20, 420))
    note = (
        f"<text x='20' y='530' font-size='11' fill='#555' {FONT}>"
        f"1 CQL partition = 1 category - hot category concentrates load.</text>"
    )
    parts.append(note)
    return svg(680, 560, "\n".join(parts))


def schema_b():
    parts = [
        f"<text x='20' y='28' font-size='17' font-weight='bold' {FONT}>"
        f"Schema B - bucketed partition per category</text>"
    ]
    tbl, th = table_svg(
        300, 50, 340, "products_bucketed",
        [
            ("category_id", "uuid", "K"),
            ("bucket", "smallint", "K"),
            ("added_at", "timestamp", "C v"),
            ("product_id", "uuid", "C ^"),
        ],
        [
            ("name", "text", ""), ("brand", "text", ""),
            ("price", "decimal", ""), ("currency", "text", ""),
            ("stock", "int", ""), ("rating", "float", ""),
            ("attributes", "map&lt;text,text&gt;", ""),
        ],
    )
    parts.append(tbl)
    tbl2, th2 = table_svg(
        300, 50 + th + 40, 340, "products_by_id",
        [("product_id", "uuid", "K")],
        [("name", "text", ""), ("brand", "text", ""), ("price", "decimal", ""),
         ("currency", "text", ""), ("stock", "int", ""), ("rating", "float", ""),
         ("attributes", "map&lt;text,text&gt;", "")],
    )
    parts.append(tbl2)
    parts.append(f"<text x='20' y='90' font-size='12' fill='#7d3c98' {FONT}>"
                 f"Q2, Q3, Q4 reads (fan-out x{NUM_BUCKETS})</text>")
    parts.append(query_arrow(40, 98, 296, 160))
    parts.append(f"<text x='20' y='130' font-size='12' fill='#7d3c98' {FONT}>"
                 f"W1, W2, W3 writes (1 bucket)</text>")
    parts.append(query_arrow(40, 138, 296, 210))
    parts.append(f"<text x='20' y='{50 + th + 110}' font-size='12' "
                 f"fill='#7d3c98' {FONT}>Q1 point lookup</text>")
    parts.append(query_arrow(40, 50 + th + 118, 296, 50 + th + 120))
    parts.append(legend(20, 430))
    parts.append(
        f"<text x='20' y='530' font-size='11' fill='#555' {FONT}>"
        f"bucket = hash(product_id) % {NUM_BUCKETS} - spreads a category "
        f"over {NUM_BUCKETS} partitions.</text>"
    )
    return svg(680, 560, "\n".join(parts))


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "schema-a.svg").write_text(schema_a())
    (OUT_DIR / "schema-b.svg").write_text(schema_b())
    print(f"wrote {OUT_DIR}/schema-a.svg and schema-b.svg")


if __name__ == "__main__":
    main()
