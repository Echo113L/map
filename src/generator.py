"""
pyecharts map generator.
Supports single-year maps and multi-year Timeline with auto-play.

Unified visualMap: both single and timeline paths use _build_visualmap()
which auto-detects tiny-value data and switches to piecewise mode.
"""

import math
import os
import tempfile
from typing import List, Dict, Tuple
from pyecharts.charts import Map, Timeline
from pyecharts import options as opts
from .themes import interpolate_light_dark


def _render_chart_to_html(chart) -> str:
    """Render any pyecharts chart to an HTML string via temp file."""
    tmp = tempfile.NamedTemporaryFile(
        suffix=".html", delete=False, mode="w", encoding="utf-8",
    )
    tmp_path = tmp.name
    tmp.close()
    try:
        chart.render(tmp_path)
        with open(tmp_path, "r", encoding="utf-8") as f:
            return f.read()
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# ── Smart visualMap ─────────────────────────────────────────────────────


def _ratio_span(vals: List[float]) -> float:
    """max/min ratio; inf if min is 0 or negative."""
    mn, mx = min(vals), max(vals)
    if mn <= 0 or mx <= 0:
        return float("inf")
    return mx / mn


def _span_is_tiny(vals: List[float]) -> bool:
    """
    True when a continuous colour ramp would make provinces look
    nearly identical.
    """
    if len(vals) < 2:
        return False
    ratio = _ratio_span(vals)
    mx = max(vals)
    # Relaxed thresholds to catch more borderline cases
    if mx <= 1:
        return ratio < 10        # e.g. 0.05 vs 0.50 → ratio=10
    if mx <= 10:
        return ratio < 5
    if mx <= 100:
        return ratio < 2.5
    return ratio < 1.4


def _build_visualmap(
    vals: List[float],
    colors: List[str],
    force_piecewise: bool = False,
) -> opts.VisualMapOpts:
    """
    Build a VisualMapOpts instance.

    Auto-detects tiny-value data → switches to piecewise buckets.
    Set force_piecewise=True to always use piecewise mode.
    """
    if not vals:
        return opts.VisualMapOpts(
            min_=0, max_=100, range_color=colors,
            pos_left="3%", pos_bottom="10%",
        )

    mn, mx = min(vals), max(vals)
    sorted_colors = interpolate_light_dark(colors)

    # Decide mode
    use_piecewise = force_piecewise or _span_is_tiny(vals)

    if use_piecewise:
        n_buckets = min(len(sorted_colors), 6)
        span = mx - mn
        if span == 0:
            span = abs(mx) * 0.1 if mx != 0 else 1

        decimals = max(0, -int(math.floor(math.log10(abs(span) + 1e-12))) + 2)
        step = span / (n_buckets - 1)
        pieces = []
        for i in range(n_buckets - 1):
            lo = round(mn + i * step, decimals)
            hi = round(mn + (i + 1) * step, decimals)
            ci = i if i < len(sorted_colors) else -1
            pieces.append({"min": lo, "max": hi, "color": sorted_colors[ci]})
        pieces.append({
            "min": round(mn + (n_buckets - 1) * step, decimals),
            "max": mx,
            "color": sorted_colors[min(n_buckets - 1, len(sorted_colors) - 1)],
        })

        return opts.VisualMapOpts(
            min_=mn, max_=mx,
            is_piecewise=True,
            pieces=pieces,
            pos_left="3%", pos_bottom="8%",
            item_width=18, item_height=12,
            textstyle_opts=opts.TextStyleOpts(font_size=10),
            orient="horizontal",
        )

    # Continuous gradient
    return opts.VisualMapOpts(
        min_=mn, max_=mx,
        range_color=sorted_colors,
        pos_left="3%", pos_bottom="10%",
        is_piecewise=False,
        textstyle_opts=opts.TextStyleOpts(font_size=11),
    )


# ── Map builders ────────────────────────────────────────────────────────


def _make_map(
    data_pairs: List[Tuple[str, float]],
    map_type: str,
    title: str,
    subtitle: str,
    range_colors: List[str],
    unit: str = "",
    show_labels: bool = True,
    force_piecewise: bool = False,
) -> Map:
    """Create a single pyecharts Map instance with smart visualMap."""
    vals = [v for _, v in data_pairs if v is not None]
    visualmap = _build_visualmap(vals, range_colors, force_piecewise=force_piecewise)

    unit_suffix = f" {unit}" if unit else ""
    tooltip_fmt = "{b}<br/>数值：{c}" + unit_suffix

    map_chart = Map(
        init_opts=opts.InitOpts(
            bg_color="#ffffff",
            animation_opts=opts.AnimationOpts(animation=True),
        ),
    )
    map_chart.add(
        series_name=title,
        data_pair=data_pairs,
        maptype=map_type,
        zoom=1.1,
        is_map_symbol_show=False,
        label_opts=opts.LabelOpts(is_show=show_labels, font_size=9),
    )
    map_chart.set_global_opts(
        title_opts=opts.TitleOpts(
            title=title or "数据分布图",
            subtitle=subtitle or "数据来源：用户上传",
            pos_left="center", pos_top="3%",
            title_textstyle_opts=opts.TextStyleOpts(font_size=20, font_weight="bold"),
            subtitle_textstyle_opts=opts.TextStyleOpts(font_size=12, color="#666"),
        ),
        visualmap_opts=visualmap,
        tooltip_opts=opts.TooltipOpts(
            trigger="item", formatter=tooltip_fmt,
            background_color="rgba(255,255,255,0.95)",
            border_color="#ddd",
            textstyle_opts=opts.TextStyleOpts(color="#333", font_size=12),
        ),
        legend_opts=opts.LegendOpts(is_show=False),
    )
    return map_chart


def generate_map_html(
    data_pairs: List[Tuple[str, float]],
    map_type: str, title: str, subtitle: str,
    range_colors: List[str],
    unit: str = "", show_labels: bool = True,
    force_piecewise: bool = False,
) -> str:
    """Generate a single static map HTML string."""
    map_chart = _make_map(
        data_pairs=data_pairs, map_type=map_type, title=title,
        subtitle=subtitle, range_colors=range_colors, unit=unit,
        show_labels=show_labels, force_piecewise=force_piecewise,
    )
    return _render_chart_to_html(map_chart)


def generate_timeline_html(
    year_data_map: Dict[str, List[Tuple[str, float]]],
    map_type: str,
    title_template: str, subtitle: str,
    range_colors: List[str],
    unit: str = "", show_labels: bool = True,
    auto_play: bool = False, play_interval: int = 3000,
    force_piecewise: bool = False,
) -> str:
    """Generate a multi-year Timeline HTML string."""

    if not year_data_map:
        return "<p>No data to display</p>"

    years = sorted(year_data_map.keys())

    # Global min/max for consistent colour scale
    all_vals = [
        v for pairs in year_data_map.values()
        for _, v in pairs if v is not None
    ]
    global_min = min(all_vals) if all_vals else 0
    global_max = max(all_vals) if all_vals else 100

    sorted_colors = interpolate_light_dark(range_colors)

    # ── Use unified visualMap logic, NOT hardcoded continuous ──
    # Use per-year min/max for the visualMap of each frame
    # (global min/max ensures cross-year colour consistency)
    visualmap = _build_visualmap(all_vals, range_colors, force_piecewise=force_piecewise)

    tl = Timeline(
        init_opts=opts.InitOpts(
            width="1200px", height="700px", bg_color="#ffffff",
            animation_opts=opts.AnimationOpts(animation=True),
        ),
    )
    tl.add_schema(
        is_auto_play=auto_play,
        play_interval=play_interval,
        pos_bottom="2%", width="85%",
        label_opts=opts.LabelOpts(font_size=12, color="#333"),
        is_loop_play=True,
    )

    for year in years:
        pairs = year_data_map[year]
        title = (
            title_template.replace("{year}", str(year))
            if "{year}" in title_template
            else f"{year} {title_template}"
        )
        unit_str = f"  单位：{unit}" if unit else ""
        year_subtitle = subtitle or f"数据来源：用户上传{unit_str}"

        tooltip_fmt = "{b}<br/>数值：{c}" + (f" {unit}" if unit else "")

        map_chart = Map(
            init_opts=opts.InitOpts(
                bg_color="#ffffff",
                animation_opts=opts.AnimationOpts(animation=True),
            ),
        )
        map_chart.add(
            series_name=title,
            data_pair=pairs,
            maptype=map_type,
            zoom=1.1,
            is_map_symbol_show=False,
            label_opts=opts.LabelOpts(is_show=show_labels, font_size=9),
        )
        map_chart.set_global_opts(
            title_opts=opts.TitleOpts(
                title=title, subtitle=year_subtitle,
                pos_left="center", pos_top="3%",
                title_textstyle_opts=opts.TextStyleOpts(font_size=20, font_weight="bold"),
                subtitle_textstyle_opts=opts.TextStyleOpts(font_size=12, color="#666"),
            ),
            visualmap_opts=visualmap,   # <-- NOW uses unified logic
            tooltip_opts=opts.TooltipOpts(
                trigger="item", formatter=tooltip_fmt,
                background_color="rgba(255,255,255,0.95)",
                border_color="#ddd",
                textstyle_opts=opts.TextStyleOpts(color="#333", font_size=12),
            ),
            legend_opts=opts.LegendOpts(is_show=False),
        )
        tl.add(map_chart, str(year))

    return _render_chart_to_html(tl)


def generate_preview_html(
    year_data_map: Dict[str, List[Tuple[str, float]]],
    map_type: str,
    title_template: str, subtitle: str,
    range_colors: List[str],
    unit: str = "", show_labels: bool = True,
    auto_play: bool = False, play_interval: int = 3000,
    force_piecewise: bool = False,
) -> Tuple[str, bool]:
    """
    Main entry point: generate map HTML.
    Returns (html_string, is_multi_year).
    """
    if not year_data_map:
        return (
            "<p style='text-align:center;padding:40px;color:#999;'>请上传CSV数据文件</p>",
            False,
        )

    years = sorted(year_data_map.keys())
    is_multi = len(years) > 1

    if is_multi:
        html = generate_timeline_html(
            year_data_map=year_data_map, map_type=map_type,
            title_template=title_template, subtitle=subtitle,
            range_colors=range_colors, unit=unit,
            show_labels=show_labels,
            auto_play=auto_play, play_interval=play_interval,
            force_piecewise=force_piecewise,
        )
    else:
        year = years[0]
        title = (
            title_template.replace("{year}", str(year))
            if "{year}" in title_template
            else title_template
        )
        html = generate_map_html(
            data_pairs=year_data_map[year],
            map_type=map_type, title=title, subtitle=subtitle,
            range_colors=range_colors, unit=unit,
            show_labels=show_labels,
            force_piecewise=force_piecewise,
        )

    return html, is_multi
