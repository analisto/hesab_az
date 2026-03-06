import sys
import os
import csv
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
DATA_FILE = os.path.join(BASE_DIR, "data", "data.csv")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

# ── Load data ──────────────────────────────────────────────────────────────────
with open(DATA_FILE, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

# ── Style ──────────────────────────────────────────────────────────────────────
BRAND_BLUE   = "#1A5276"
BRAND_TEAL   = "#148F77"
BRAND_AMBER  = "#D4AC0D"
BRAND_RED    = "#C0392B"
BRAND_GRAY   = "#808B96"
BRAND_LIGHT  = "#D6EAF8"

TIER_COLORS = {
    "Established": BRAND_BLUE,
    "Growing":     BRAND_TEAL,
    "Emerging":    BRAND_AMBER,
}

plt.rcParams.update({
    "figure.facecolor":  "white",
    "axes.facecolor":    "white",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "axes.grid.axis":    "x",
    "grid.color":        "#E8E8E8",
    "grid.linewidth":    0.8,
    "font.family":       "sans-serif",
    "font.size":         11,
    "axes.titlesize":    14,
    "axes.titleweight":  "bold",
    "axes.labelsize":    11,
})

def save(fig, name):
    path = os.path.join(CHARTS_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: charts/{name}")


# ══════════════════════════════════════════════════════════════════════════════
# Chart 1 – Merchant Count by Category (horizontal bar, sorted)
# ══════════════════════════════════════════════════════════════════════════════
cat_counts = Counter(r["_category_name"] for r in rows)
cats_sorted = sorted(cat_counts.items(), key=lambda x: x[1])
names  = [c[0] for c in cats_sorted]
counts = [c[1] for c in cats_sorted]
total  = sum(counts)

# Assign tier colours
def tier(n):
    if n >= 30: return "Established"
    if n >= 15: return "Growing"
    return "Emerging"

bar_colors = [TIER_COLORS[tier(n)] for n in counts]

fig, ax = plt.subplots(figsize=(11, 7))
bars = ax.barh(names, counts, color=bar_colors, edgecolor="white", height=0.65)

for bar, val in zip(bars, counts):
    ax.text(val + 0.8, bar.get_y() + bar.get_height() / 2,
            f"{val}  ({val/total*100:.0f}%)",
            va="center", fontsize=9.5, color="#333333")

patches = [mpatches.Patch(color=TIER_COLORS[t], label=f"{t} (30+, 15–29, <15)")
           for t in ("Established", "Growing", "Emerging")]
# Cleaner legend labels
legend_labels = [
    mpatches.Patch(color=TIER_COLORS["Established"], label="Established  (≥30 merchants)"),
    mpatches.Patch(color=TIER_COLORS["Growing"],     label="Growing      (15–29 merchants)"),
    mpatches.Patch(color=TIER_COLORS["Emerging"],    label="Emerging     (<15 merchants)"),
]
ax.legend(handles=legend_labels, loc="lower right", fontsize=9, framealpha=0.9)
ax.set_xlabel("Number of Merchants on Platform")
ax.set_title("Platform Coverage: Merchant Count by Service Category")
ax.set_xlim(0, max(counts) * 1.22)
fig.tight_layout()
save(fig, "01_merchant_count_by_category.png")


# ══════════════════════════════════════════════════════════════════════════════
# Chart 2 – Merchant Type Composition (stacked bar per category, sorted by total)
# ══════════════════════════════════════════════════════════════════════════════
type_by_cat = defaultdict(lambda: {"LARGE_MERCHANT": 0, "Subcategory": 0})
for r in rows:
    type_by_cat[r["_category_name"]][r["type"]] += 1

# Sort by total descending
sorted_cats = sorted(type_by_cat.items(), key=lambda x: sum(x[1].values()), reverse=True)
sc_names  = [x[0] for x in sorted_cats]
large_vals = [x[1]["LARGE_MERCHANT"] for x in sorted_cats]
sub_vals   = [x[1]["Subcategory"]    for x in sorted_cats]

x = np.arange(len(sc_names))
width = 0.55

fig, ax = plt.subplots(figsize=(13, 6))
b1 = ax.bar(x, large_vals, width, label="Direct Merchant", color=BRAND_BLUE,   edgecolor="white")
b2 = ax.bar(x, sub_vals,   width, label="Sub-service Group", color=BRAND_TEAL, edgecolor="white",
            bottom=large_vals)

for xi, (lv, sv) in enumerate(zip(large_vals, sub_vals)):
    total_v = lv + sv
    ax.text(xi, total_v + 0.7, str(total_v), ha="center", va="bottom", fontsize=9, fontweight="bold")
    if sv > 0:
        ax.text(xi, lv + sv / 2, str(sv), ha="center", va="center", fontsize=8,
                color="white", fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(sc_names, rotation=35, ha="right", fontsize=9.5)
ax.set_ylabel("Number of Merchants")
ax.set_title("Service Complexity: Direct Merchants vs. Sub-service Groups by Category")
ax.legend(loc="upper right", fontsize=10)
ax.set_xlim(-0.5, len(sc_names) - 0.5)
ax.grid(axis="y", color="#E8E8E8")
ax.set_axisbelow(True)
ax.spines["left"].set_visible(False)
fig.tight_layout()
save(fig, "02_merchant_type_composition.png")


# ══════════════════════════════════════════════════════════════════════════════
# Chart 3 – Market Concentration: Top 5 vs. Rest
# ══════════════════════════════════════════════════════════════════════════════
sorted_desc = sorted(cat_counts.items(), key=lambda x: -x[1])
top5   = sorted_desc[:5]
others = sorted_desc[5:]
other_total = sum(v for _, v in others)

chart_items  = top5 + [("All Other Categories\n(12 categories)", other_total)]
chart_labels = [c[0] for c in chart_items]
chart_vals   = [c[1] for c in chart_items]
chart_pcts   = [v / total * 100 for v in chart_vals]
chart_colors = [BRAND_BLUE, BRAND_BLUE, BRAND_BLUE, BRAND_BLUE, BRAND_BLUE, BRAND_GRAY]

fig, ax = plt.subplots(figsize=(11, 5.5))
bars = ax.bar(chart_labels, chart_vals, color=chart_colors, edgecolor="white", width=0.6)

for bar, val, pct in zip(bars, chart_vals, chart_pcts):
    ax.text(bar.get_x() + bar.get_width() / 2, val + 1.2,
            f"{val}\n({pct:.0f}%)", ha="center", va="bottom", fontsize=10, fontweight="bold")

ax.set_ylabel("Number of Merchants")
ax.set_title("Market Concentration: Top 5 Categories Dominate the Platform")
ax.tick_params(axis="x", labelsize=9.5)
ax.set_ylim(0, max(chart_vals) * 1.2)

# Annotation: top 5 share
top5_share = sum(v for _, v in top5) / total * 100
ax.axhline(0, color="black", linewidth=0.5)
ax.annotate(f"Top 5 categories = {top5_share:.0f}% of all merchants",
            xy=(0.5, 0.93), xycoords="axes fraction",
            ha="center", fontsize=10, color=BRAND_BLUE,
            bbox=dict(boxstyle="round,pad=0.3", facecolor=BRAND_LIGHT, edgecolor=BRAND_BLUE, alpha=0.8))
fig.tight_layout()
save(fig, "03_market_concentration.png")


# ══════════════════════════════════════════════════════════════════════════════
# Chart 4 – Strategic Growth Gap: Emerging Categories
# ══════════════════════════════════════════════════════════════════════════════
# Show all categories sized against what "benchmark" coverage looks like
# Benchmark: average of Established tier
established = [v for _, v in cat_counts.items() if v >= 30]
benchmark = int(np.mean(established)) if established else 30

all_sorted_desc = sorted(cat_counts.items(), key=lambda x: -x[1])
gc_names  = [c[0] for c in all_sorted_desc]
gc_counts = [c[1] for c in all_sorted_desc]
gc_colors = [TIER_COLORS[tier(v)] for v in gc_counts]
gc_gaps   = [max(0, benchmark - v) for v in gc_counts]

fig, ax = plt.subplots(figsize=(12, 6))
x = np.arange(len(gc_names))
width = 0.55

b_actual = ax.bar(x, gc_counts, width, color=gc_colors, edgecolor="white", label="Current Merchants")
b_gap    = ax.bar(x, gc_gaps,   width, bottom=gc_counts, color="#EAEDED",
                  edgecolor="#BDC3C7", linewidth=0.5, label=f"Gap to Platform Average ({benchmark})")

ax.axhline(benchmark, color=BRAND_RED, linewidth=1.5, linestyle="--",
           label=f"Platform average (established tier): {benchmark}")

for xi, val in enumerate(gc_counts):
    ax.text(xi, val / 2, str(val), ha="center", va="center", fontsize=8.5,
            color="white", fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(gc_names, rotation=38, ha="right", fontsize=9)
ax.set_ylabel("Number of Merchants")
ax.set_title("Strategic Growth Gap: Current Coverage vs. Platform Average by Category")
ax.legend(loc="upper right", fontsize=9.5)
ax.set_ylim(0, benchmark * 1.7)
ax.set_axisbelow(True)
fig.tight_layout()
save(fig, "04_growth_gap_analysis.png")


# ══════════════════════════════════════════════════════════════════════════════
# Chart 5 – Digital Feature Adoption (NFC & Deep-Linked Merchants)
# ══════════════════════════════════════════════════════════════════════════════
# NFC = 0 everywhere, links = 2 total → show per category totals vs digital features
digital_by_cat = defaultdict(lambda: {"total": 0, "nfc": 0, "linked": 0})
for r in rows:
    cat = r["_category_name"]
    digital_by_cat[cat]["total"] += 1
    if r["nfc"] == "True":
        digital_by_cat[cat]["nfc"] += 1
    if r["link"] and r["link"].strip():
        digital_by_cat[cat]["linked"] += 1

dc_sorted = sorted(digital_by_cat.items(), key=lambda x: -x[1]["total"])
dc_names  = [x[0] for x in dc_sorted]
dc_total  = [x[1]["total"]  for x in dc_sorted]
dc_nfc    = [x[1]["nfc"]    for x in dc_sorted]
dc_linked = [x[1]["linked"] for x in dc_sorted]

x = np.arange(len(dc_names))
width = 0.28

fig, ax = plt.subplots(figsize=(13, 6))
ax.bar(x - width, dc_total,  width, label="Total Merchants",     color=BRAND_GRAY,  edgecolor="white")
ax.bar(x,         dc_linked, width, label="Deep-Linked (URL)",   color=BRAND_AMBER, edgecolor="white")
ax.bar(x + width, dc_nfc,    width, label="NFC-Enabled",         color=BRAND_RED,   edgecolor="white")

ax.set_xticks(x)
ax.set_xticklabels(dc_names, rotation=38, ha="right", fontsize=9)
ax.set_ylabel("Number of Merchants")
ax.set_title("Digital Feature Adoption: NFC & Deep-Link Enablement Across Categories")
ax.legend(fontsize=10)

# Add callout
ax.annotate("0 NFC-enabled merchants\nacross all 17 categories",
            xy=(0.72, 0.82), xycoords="axes fraction",
            fontsize=10, color=BRAND_RED, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#FDEDEC", edgecolor=BRAND_RED, alpha=0.9))
ax.set_axisbelow(True)
fig.tight_layout()
save(fig, "05_digital_feature_adoption.png")


# ══════════════════════════════════════════════════════════════════════════════
# Chart 6 – Priority Ordering Coverage (Merchant Discoverability)
# ══════════════════════════════════════════════════════════════════════════════
MAX_ORDER = 2147483647
ordered_by_cat   = defaultdict(int)
unordered_by_cat = defaultdict(int)

for r in rows:
    cat = r["_category_name"]
    try:
        o = int(r["orderNo"])
    except (ValueError, TypeError):
        o = MAX_ORDER
    if o == MAX_ORDER:
        unordered_by_cat[cat] += 1
    else:
        ordered_by_cat[cat] += 1

all_cats = sorted(cat_counts.keys(), key=lambda c: -cat_counts[c])
ord_vals   = [ordered_by_cat.get(c, 0)   for c in all_cats]
unord_vals = [unordered_by_cat.get(c, 0) for c in all_cats]

x = np.arange(len(all_cats))
width = 0.55

fig, ax = plt.subplots(figsize=(13, 6))
b1 = ax.bar(x, ord_vals,   width, label="Priority Ranked",   color=BRAND_TEAL, edgecolor="white")
b2 = ax.bar(x, unord_vals, width, bottom=ord_vals,
            label="No Priority Set (hidden from ranking)", color="#D5D8DC", edgecolor="#BDC3C7", linewidth=0.5)

for xi, (ov, uv) in enumerate(zip(ord_vals, unord_vals)):
    total_v = ov + uv
    if ov > 0:
        ax.text(xi, ov / 2, str(ov), ha="center", va="center", fontsize=8, color="white", fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(all_cats, rotation=38, ha="right", fontsize=9)
ax.set_ylabel("Number of Merchants")
ax.set_title("Merchant Discoverability: Priority-Ranked vs. Unranked Listings")
ax.legend(fontsize=10)

total_ordered = sum(ord_vals)
total_unordered = sum(unord_vals)
ax.annotate(f"Only {total_ordered} of {total} merchants ({total_ordered/total*100:.0f}%) have\na defined display priority",
            xy=(0.62, 0.84), xycoords="axes fraction",
            fontsize=10, color=BRAND_BLUE, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.4", facecolor=BRAND_LIGHT, edgecolor=BRAND_BLUE, alpha=0.9))
ax.set_axisbelow(True)
fig.tight_layout()
save(fig, "06_merchant_discoverability.png")


print(f"\nAll 6 charts saved to charts/")
