"""
generate_charts.py
Reads data/cosmetics.csv and writes business insight charts to charts/.
"""

import collections
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# ── Config ──────────────────────────────────────────────────────────────────
DATA_PATH = Path("data/cosmetics.csv")
OUT_DIR = Path("charts")
OUT_DIR.mkdir(exist_ok=True)

BRAND_COLOR = "#2563EB"      # primary blue
ACCENT = "#F59E0B"           # amber accent
SOFT = "#93C5FD"             # light blue
DANGER = "#EF4444"           # red
SUCCESS = "#10B981"          # green
BG = "#F8FAFC"
GRID = "#E2E8F0"

FONT_TITLE = {"fontsize": 14, "fontweight": "bold", "color": "#1E293B"}
FONT_LABEL = {"fontsize": 11, "color": "#475569"}
FONT_TICK = {"labelsize": 10, "labelcolor": "#475569"}

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "axes.edgecolor": GRID,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "grid.color": GRID,
    "grid.linestyle": "--",
    "grid.alpha": 0.8,
    "font.family": "DejaVu Sans",
})


def _save(fig: plt.Figure, name: str) -> None:
    path = OUT_DIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  saved -> {path}")


def _fmt_k(x, _):
    if x >= 1000:
        return f"{x/1000:.0f}k"
    return f"{x:.0f}"


# ── Load ─────────────────────────────────────────────────────────────────────
print("Loading data…")
with open(DATA_PATH, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

total = len(rows)
print(f"  {total:,} products loaded")


# ============================================================
# CHART 1 — Top 15 Categories by Product Count
# ============================================================
print("Chart 1: Category volume…")
cat_count: dict[str, int] = collections.Counter(r["category_name"] for r in rows)
top_cats = cat_count.most_common(15)
labels = [c[0] for c in top_cats][::-1]
values = [c[1] for c in top_cats][::-1]
colors = [BRAND_COLOR if i < 12 else ACCENT for i in range(len(labels))]
colors[0] = ACCENT  # highlight the top bar (now at top after reverse)

fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.barh(labels, values, color=colors[::-1], height=0.65)
ax.set_xlabel("Number of Products", **FONT_LABEL)
ax.set_title("Top 15 Product Categories by Volume", **FONT_TITLE, pad=14)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(_fmt_k))
ax.tick_params(**FONT_TICK)
ax.set_xlim(0, max(values) * 1.18)
for bar, val in zip(bars, values):
    ax.text(bar.get_width() + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
            f"{val:,}", va="center", ha="left", fontsize=9, color="#475569")
ax.axvline(0, color=GRID)
fig.tight_layout()
_save(fig, "01_category_volume.png")


# ============================================================
# CHART 2 — Retail Price Band Distribution
# ============================================================
print("Chart 2: Price bands…")
bands = ["< 5", "5 – 15", "15 – 30", "30 – 60", "60 – 100", "100 – 200", "200+"]
thresholds = [5, 15, 30, 60, 100, 200]
band_counts = [0] * len(bands)
for r in rows:
    if not r["retail_price"]:
        continue
    p = float(r["retail_price"])
    if p < 5:
        band_counts[0] += 1
    elif p < 15:
        band_counts[1] += 1
    elif p < 30:
        band_counts[2] += 1
    elif p < 60:
        band_counts[3] += 1
    elif p < 100:
        band_counts[4] += 1
    elif p < 200:
        band_counts[5] += 1
    else:
        band_counts[6] += 1

pcts = [v / total * 100 for v in band_counts]
fig, ax = plt.subplots(figsize=(11, 6))
bar_colors = [BRAND_COLOR] * len(bands)
bar_colors[1] = ACCENT   # 5-15 is biggest bucket
bars = ax.bar(bands, band_counts, color=bar_colors, width=0.65)
ax.set_xlabel("Price Range (AZN)", **FONT_LABEL)
ax.set_ylabel("Number of Products", **FONT_LABEL)
ax.set_title("Product Distribution Across Price Bands", **FONT_TITLE, pad=14)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(_fmt_k))
ax.tick_params(**FONT_TICK)
for bar, cnt, pct in zip(bars, band_counts, pcts):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 200,
            f"{cnt:,}\n({pct:.1f}%)", ha="center", va="bottom", fontsize=9, color="#475569")
ax.set_ylim(0, max(band_counts) * 1.20)
ax.yaxis.grid(True)
ax.set_axisbelow(True)
fig.tight_layout()
_save(fig, "02_price_bands.png")


# ============================================================
# CHART 3 — Discount Depth Distribution
# ============================================================
print("Chart 3: Discount depth…")
disc_buckets = ["0 – 10%", "10 – 20%", "20 – 30%", "30 – 50%", "50 – 70%", "70%+"]
disc_counts = [0] * 6
for r in rows:
    if not r["old_price"] or not r["retail_price"]:
        continue
    op, rp = float(r["old_price"]), float(r["retail_price"])
    if op <= rp or op == 0:
        continue
    d = (op - rp) / op * 100
    if d < 10:
        disc_counts[0] += 1
    elif d < 20:
        disc_counts[1] += 1
    elif d < 30:
        disc_counts[2] += 1
    elif d < 50:
        disc_counts[3] += 1
    elif d < 70:
        disc_counts[4] += 1
    else:
        disc_counts[5] += 1

not_discounted = total - sum(disc_counts)
disc_pcts = [v / total * 100 for v in disc_counts]

fig, ax = plt.subplots(figsize=(11, 6))
bar_colors = [SOFT, SOFT, BRAND_COLOR, BRAND_COLOR, ACCENT, DANGER]
bars = ax.bar(disc_buckets, disc_counts, color=bar_colors, width=0.65)
ax.set_xlabel("Discount Depth", **FONT_LABEL)
ax.set_ylabel("Number of Products", **FONT_LABEL)
ax.set_title(f"Discount Depth Distribution  ·  {sum(disc_counts):,} discounted products ({sum(disc_counts)/total*100:.1f}% of catalog)", **FONT_TITLE, pad=14)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(_fmt_k))
ax.tick_params(**FONT_TICK)
for bar, cnt, pct in zip(bars, disc_counts, disc_pcts):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 150,
            f"{cnt:,}\n({pct:.1f}%)", ha="center", va="bottom", fontsize=9, color="#475569")
ax.set_ylim(0, max(disc_counts) * 1.22)
ax.yaxis.grid(True)
ax.set_axisbelow(True)
fig.tight_layout()
_save(fig, "03_discount_depth.png")


# ============================================================
# CHART 4 — Top 15 Sellers by Product Count
# ============================================================
print("Chart 4: Top sellers…")
seller_products: dict[str, list[float]] = collections.defaultdict(list)
for r in rows:
    if r["seller_name"] and r["retail_price"]:
        seller_products[r["seller_name"]].append(float(r["retail_price"]))

top_sellers = sorted(seller_products.items(), key=lambda x: len(x[1]), reverse=True)[:15]
s_labels = [s[0] for s in top_sellers][::-1]
s_counts = [len(s[1]) for s in top_sellers][::-1]
s_avg_prices = [sum(s[1]) / len(s[1]) for s in top_sellers][::-1]

fig, ax1 = plt.subplots(figsize=(13, 7))
bars = ax1.barh(s_labels, s_counts, color=BRAND_COLOR, height=0.60)
ax1.set_xlabel("Number of Products", **FONT_LABEL)
ax1.set_title("Top 15 Sellers by Product Volume", **FONT_TITLE, pad=14)
ax1.xaxis.set_major_formatter(mticker.FuncFormatter(_fmt_k))
ax1.tick_params(**FONT_TICK)
ax1.set_xlim(0, max(s_counts) * 1.30)
for bar, cnt, avg_p in zip(bars, s_counts, s_avg_prices):
    ax1.text(bar.get_width() + max(s_counts) * 0.01,
             bar.get_y() + bar.get_height() / 2,
             f"{cnt:,} products  ·  avg AZN {avg_p:.0f}",
             va="center", ha="left", fontsize=8.5, color="#475569")
ax1.axvline(0, color=GRID)
fig.tight_layout()
_save(fig, "04_top_sellers.png")


# ============================================================
# CHART 5 — Seller Rating Distribution
# ============================================================
print("Chart 5: Seller ratings…")
rating_bands = ["0 – 60", "60 – 75", "75 – 85", "85 – 90", "90 – 95", "95 – 100"]
rating_counts = [0] * 6
for r in rows:
    if not r["seller_rating"]:
        continue
    sr = int(r["seller_rating"])
    if sr < 60:
        rating_counts[0] += 1
    elif sr < 75:
        rating_counts[1] += 1
    elif sr < 85:
        rating_counts[2] += 1
    elif sr < 90:
        rating_counts[3] += 1
    elif sr < 95:
        rating_counts[4] += 1
    else:
        rating_counts[5] += 1

r_pcts = [v / total * 100 for v in rating_counts]
fig, ax = plt.subplots(figsize=(11, 6))
bar_colors = [DANGER, DANGER, SOFT, SOFT, BRAND_COLOR, SUCCESS]
bars = ax.bar(rating_bands, rating_counts, color=bar_colors, width=0.65)
ax.set_xlabel("Seller Rating Band", **FONT_LABEL)
ax.set_ylabel("Number of Products", **FONT_LABEL)
ax.set_title("Products by Seller Quality Rating", **FONT_TITLE, pad=14)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(_fmt_k))
ax.tick_params(**FONT_TICK)
for bar, cnt, pct in zip(bars, rating_counts, r_pcts):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 400,
            f"{cnt:,}\n({pct:.1f}%)", ha="center", va="bottom", fontsize=9, color="#475569")
ax.set_ylim(0, max(rating_counts) * 1.20)
ax.yaxis.grid(True)
ax.set_axisbelow(True)
fig.tight_layout()
_save(fig, "05_seller_ratings.png")


# ============================================================
# CHART 6 — Top 15 Brands by Product Count (excl. No Brand)
# ============================================================
print("Chart 6: Top brands…")
brand_count: dict[str, int] = collections.Counter()
for r in rows:
    b = r["brand"].strip()
    if b and b.lower() not in ("no brand",):
        brand_count[b] += 1
top_brands = brand_count.most_common(15)
b_labels = [b[0] for b in top_brands][::-1]
b_values = [b[1] for b in top_brands][::-1]

fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.barh(b_labels, b_values, color=BRAND_COLOR, height=0.65)
ax.set_xlabel("Number of Products", **FONT_LABEL)
ax.set_title("Top 15 Named Brands by Product Volume", **FONT_TITLE, pad=14)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(_fmt_k))
ax.tick_params(**FONT_TICK)
ax.set_xlim(0, max(b_values) * 1.22)
for bar, val in zip(bars, b_values):
    ax.text(bar.get_width() + max(b_values) * 0.01, bar.get_y() + bar.get_height() / 2,
            f"{val:,}", va="center", ha="left", fontsize=9, color="#475569")
ax.axvline(0, color=GRID)
fig.tight_layout()
_save(fig, "06_top_brands.png")


# ============================================================
# CHART 7 — Installment Plan Duration
# ============================================================
print("Chart 7: Installment durations…")
inst_counter: dict[str, int] = collections.Counter(r["max_installment_months"] for r in rows)
inst_order = ["3", "6", "9", "12", "18", "24"]
inst_labels = [f"{m} months" for m in inst_order]
inst_values = [inst_counter.get(m, 0) for m in inst_order]
inst_pcts = [v / total * 100 for v in inst_values]

fig, ax = plt.subplots(figsize=(11, 6))
bar_colors = [SOFT, SOFT, SOFT, BRAND_COLOR, ACCENT, SOFT]
bars = ax.bar(inst_labels, inst_values, color=bar_colors, width=0.65)
ax.set_xlabel("Maximum Installment Duration", **FONT_LABEL)
ax.set_ylabel("Number of Products", **FONT_LABEL)
ax.set_title("Installment Plan Duration Distribution", **FONT_TITLE, pad=14)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(_fmt_k))
ax.tick_params(**FONT_TICK)
for bar, cnt, pct in zip(bars, inst_values, inst_pcts):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 300,
            f"{cnt:,}\n({pct:.1f}%)", ha="center", va="bottom", fontsize=9, color="#475569")
ax.set_ylim(0, max(inst_values) * 1.22)
ax.yaxis.grid(True)
ax.set_axisbelow(True)
fig.tight_layout()
_save(fig, "07_installment_duration.png")


# ============================================================
# CHART 8 — Seller Size Segmentation
# ============================================================
print("Chart 8: Seller size segments…")
seller_count_map: dict[str, int] = collections.Counter(r["seller_name"] for r in rows if r["seller_name"])
seg_labels = ["Micro\n(1 – 9)", "Small\n(10 – 99)", "Medium\n(100 – 499)", "Large\n(500 – 999)", "Power\n(1,000+)"]
seg_thresholds = [(1, 9), (10, 99), (100, 499), (500, 999), (1000, 99999)]
seg_seller_counts = []
seg_product_counts = []
for lo, hi in seg_thresholds:
    sellers_in_seg = [k for k, v in seller_count_map.items() if lo <= v <= hi]
    seg_seller_counts.append(len(sellers_in_seg))
    seg_product_counts.append(sum(seller_count_map[s] for s in sellers_in_seg))

x = np.arange(len(seg_labels))
width = 0.38

fig, ax1 = plt.subplots(figsize=(12, 6))
ax2 = ax1.twinx()
b1 = ax1.bar(x - width / 2, seg_seller_counts, width, color=BRAND_COLOR, label="# of Sellers")
b2 = ax2.bar(x + width / 2, seg_product_counts, width, color=ACCENT, label="# of Products")
ax1.set_xticks(x)
ax1.set_xticklabels(seg_labels, fontsize=10, color="#475569")
ax1.set_ylabel("Number of Sellers", **FONT_LABEL)
ax2.set_ylabel("Number of Products", **FONT_LABEL)
ax1.set_title("Seller Ecosystem — Seller Count vs. Product Volume by Segment", **FONT_TITLE, pad=14)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(_fmt_k))
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(_fmt_k))
ax1.tick_params(**FONT_TICK)
ax2.tick_params(**FONT_TICK)
for bar, val in zip(b1, seg_seller_counts):
    ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
             f"{val}", ha="center", va="bottom", fontsize=9, color="#475569")
for bar, val in zip(b2, seg_product_counts):
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 80,
             f"{val:,}", ha="center", va="bottom", fontsize=9, color="#475569")
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=9)
fig.tight_layout()
_save(fig, "08_seller_segments.png")


# ============================================================
# CHART 9 — Average Price by Top 15 Categories
# ============================================================
print("Chart 9: Category avg price…")
cat_prices: dict[str, list[float]] = collections.defaultdict(list)
for r in rows:
    if r["category_name"] and r["retail_price"]:
        cat_prices[r["category_name"]].append(float(r["retail_price"]))

# Use same top-15 categories from chart 1
top_cat_names = [c[0] for c in cat_count.most_common(15)]
cp_labels = top_cat_names[::-1]
cp_values = [sum(cat_prices[c]) / len(cat_prices[c]) for c in top_cat_names][::-1]

fig, ax = plt.subplots(figsize=(12, 7))
bar_colors = [ACCENT if v > 50 else BRAND_COLOR for v in cp_values]
bars = ax.barh(cp_labels, cp_values, color=bar_colors, height=0.65)
ax.set_xlabel("Average Retail Price (AZN)", **FONT_LABEL)
ax.set_title("Average Product Price — Top 15 Categories by Volume", **FONT_TITLE, pad=14)
ax.tick_params(**FONT_TICK)
ax.set_xlim(0, max(cp_values) * 1.22)
for bar, val in zip(bars, cp_values):
    ax.text(bar.get_width() + max(cp_values) * 0.01, bar.get_y() + bar.get_height() / 2,
            f"AZN {val:.1f}", va="center", ha="left", fontsize=9, color="#475569")
ax.axvline(0, color=GRID)
fig.tight_layout()
_save(fig, "09_category_avg_price.png")


# ============================================================
# CHART 10 — Review Coverage Rate by Top 15 Categories
# ============================================================
print("Chart 10: Review coverage…")
cat_reviewed: dict[str, int] = collections.defaultdict(int)
cat_total: dict[str, int] = collections.defaultdict(int)
for r in rows:
    cn = r["category_name"]
    cat_total[cn] += 1
    if r["review_count"] and int(r["review_count"]) > 0:
        cat_reviewed[cn] += 1

rc_labels = top_cat_names[::-1]
rc_values = [(cat_reviewed[c] / cat_total[c] * 100) for c in top_cat_names][::-1]

fig, ax = plt.subplots(figsize=(12, 7))
bar_colors = [SUCCESS if v > 15 else (BRAND_COLOR if v > 8 else SOFT) for v in rc_values]
bars = ax.barh(rc_labels, rc_values, color=bar_colors, height=0.65)
ax.set_xlabel("% of Products with At Least One Review", **FONT_LABEL)
ax.set_title("Customer Review Coverage — Top 15 Categories", **FONT_TITLE, pad=14)
ax.tick_params(**FONT_TICK)
ax.set_xlim(0, max(rc_values) * 1.28)
ax.axvline(total / total * (sum(1 for r in rows if r["review_count"] and int(r["review_count"]) > 0) / total * 100),
           color=DANGER, linestyle="--", linewidth=1.2, label="Overall avg")
for bar, val in zip(bars, rc_values):
    ax.text(bar.get_width() + max(rc_values) * 0.01, bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}%", va="center", ha="left", fontsize=9, color="#475569")
ax.axvline(0, color=GRID)
ax.legend(fontsize=9)
fig.tight_layout()
_save(fig, "10_review_coverage.png")


# ============================================================
# CHART 11 — 3P vs FBU: Price & Discount Comparison
# ============================================================
print("Chart 11: 3P vs FBU…")
role_prices: dict[str, list[float]] = collections.defaultdict(list)
role_discounts: dict[str, list[float]] = collections.defaultdict(list)
for r in rows:
    role = r["seller_role"]
    if r["retail_price"]:
        role_prices[role].append(float(r["retail_price"]))
    if r["old_price"] and r["retail_price"]:
        op, rp = float(r["old_price"]), float(r["retail_price"])
        if op > rp > 0:
            role_discounts[role].append((op - rp) / op * 100)

roles = ["3P", "FBU"]
avg_prices = [sum(role_prices[r]) / len(role_prices[r]) for r in roles]
avg_discounts = [sum(role_discounts[r]) / len(role_discounts[r]) if role_discounts[r] else 0 for r in roles]
product_counts = [len(role_prices[r]) for r in roles]

x = np.arange(2)
width = 0.28

fig, ax1 = plt.subplots(figsize=(10, 6))
ax2 = ax1.twinx()
b1 = ax1.bar(x - width, product_counts, width, color=BRAND_COLOR, label="Product Count")
ax_prices = ax1.twinx()
ax_prices.spines["right"].set_position(("axes", 1.12))
b2 = ax_prices.bar(x, avg_prices, width, color=ACCENT, label="Avg Price (AZN)")
b3 = ax2.bar(x + width, avg_discounts, width, color=SUCCESS, label="Avg Discount %")

ax1.set_xticks(x)
ax1.set_xticklabels(["3P (Third-party Sellers)", "FBU (Fulfilled by Umico)"], fontsize=11, color="#475569")
ax1.set_ylabel("Product Count", **FONT_LABEL)
ax2.set_ylabel("Avg Discount (%)", **FONT_LABEL)
ax_prices.set_ylabel("Avg Price (AZN)", **FONT_LABEL)
ax1.set_title("Seller Model Comparison — 3P vs FBU", **FONT_TITLE, pad=14)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(_fmt_k))
ax1.tick_params(**FONT_TICK)
ax2.tick_params(**FONT_TICK)
ax_prices.tick_params(**FONT_TICK)

for bar, val in zip(b1, product_counts):
    ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.02,
             f"{val:,}", ha="center", va="bottom", fontsize=9, color="#475569")
for bar, val in zip(b2, avg_prices):
    ax_prices.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.02,
                   f"AZN {val:.0f}", ha="center", va="bottom", fontsize=9, color="#475569")
for bar, val in zip(b3, avg_discounts):
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.02,
             f"{val:.1f}%", ha="center", va="bottom", fontsize=9, color="#475569")

handles = [b1, b2, b3]
labels_legend = ["Product Count", "Avg Price (AZN)", "Avg Discount %"]
ax1.legend(handles, labels_legend, loc="upper right", fontsize=9)
fig.tight_layout()
_save(fig, "11_3p_vs_fbu.png")


# ============================================================
# CHART 12 — Top 10 Sellers: Product Count + Avg Price (grouped bar)
# ============================================================
print("Chart 12: Top 10 sellers deep dive…")
top10_sellers = sorted(seller_products.items(), key=lambda x: len(x[1]), reverse=True)[:10]
t10_labels = [s[0] for s in top10_sellers]
t10_counts = [len(s[1]) for s in top10_sellers]
t10_avg_prices = [sum(s[1]) / len(s[1]) for s in top10_sellers]

x = np.arange(len(t10_labels))
width = 0.38

fig, ax1 = plt.subplots(figsize=(14, 6))
ax2 = ax1.twinx()
b1 = ax1.bar(x - width / 2, t10_counts, width, color=BRAND_COLOR, label="Product Count")
b2 = ax2.bar(x + width / 2, t10_avg_prices, width, color=ACCENT, label="Avg Price (AZN)")
ax1.set_xticks(x)
ax1.set_xticklabels(t10_labels, rotation=28, ha="right", fontsize=9, color="#475569")
ax1.set_ylabel("Number of Products", **FONT_LABEL)
ax2.set_ylabel("Average Price (AZN)", **FONT_LABEL)
ax1.set_title("Top 10 Sellers — Product Volume vs. Average Price", **FONT_TITLE, pad=14)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(_fmt_k))
ax1.tick_params(**FONT_TICK)
ax2.tick_params(**FONT_TICK)
for bar, val in zip(b1, t10_counts):
    ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 20,
             f"{val:,}", ha="center", va="bottom", fontsize=8, color="#475569")
for bar, val in zip(b2, t10_avg_prices):
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
             f"AZN {val:.0f}", ha="center", va="bottom", fontsize=8, color="#475569")
lines1, lbl1 = ax1.get_legend_handles_labels()
lines2, lbl2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, lbl1 + lbl2, loc="upper right", fontsize=9)
fig.tight_layout()
_save(fig, "12_top10_sellers_deep.png")


print(f"\nAll charts saved to {OUT_DIR}/")
