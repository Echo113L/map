"""
pyecharts map generator.
Supports single-year maps and multi-year Timeline with auto-play.

Uses render() to temp file (not render_embed()) for maximum compatibility
with Streamlit Cloud iframe embedding.
"""

import os
import tempfile
from typing import List, Dict, Optional, Tuple
from pyecharts.charts import Map, Timeline
from pyecharts import options as opts
from pyecharts.globals import CurrentConfig

from .themes import interpolate_light_dark


def _render_chart_to_html(chart) -> str:
    """
    Render any pyecharts chart to an HTML string using a temp file.
    Uses the same render() approach as the original 分析.py for reliability.
    """
    tmp = tempfile.NamedTemporaryFile(
        suffix=".html",
        delete=False,
        mode="w",
        encoding="utf-8",
    )
    tmp_path = tmp.name
    tmp.close()

    try:
        chart.render(tmp_path)
        with open(tmp_path, "r", encoding="utf-8") as f:
            html = f.read()
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return html


def _make_map(
    data_pairs: List[Tuple[str, float]],
    map_type: str,
    title: str,
    subtitle: str,
    min_val: float,
    max_val: float,
    range_colors: List[str],
    unit: str = "",
    show_labels: bool = True,
) -> Map:
    """Create a single pyecharts Map instance."""

    # Format tooltip with unit
    if unit:
        tooltip_fmt = "{b}<br/>" + title + "：{c} " + unit
    else:
        tooltip_fmt = "{b}<br/>" + title + "：{c}"

    # Sort colors so lighter comes first (for VisualMap)
    sorted_colors = interpolate_light_dark(range_colors)

    map_chart = Map(
        init_opts=opts.InitOpts(
            bg_color="#ffffff",
            animation_opts=opts.AnimationOpts(animation=True),
        )
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
            title=title if title else "数据分布图",
            subtitle=subtitle or "数据来源：用户上传",
            pos_left="center",
            pos_top="3%",
            title_textstyle_opts=opts.TextStyleOpts(font_size=20, font_weight="bold"),
            subtitle_textstyle_opts=opts.TextStyleOpts(font_size=12, color="#666"),
        ),
        visualmap_opts=opts.VisualMapOpts(
            min_=min_val,
            max_=max_val,
            range_color=sorted_colors,
            pos_left="3%",
            pos_bottom="10%",
            is_piecewise=False,
            textstyle_opts=opts.TextStyleOpts(font_size=11),
        ),
        tooltip_opts=opts.TooltipOpts(
            trigger="item",
            formatter=tooltip_fmt,
            background_color="rgba(255,255,255,0.95)",
            border_color="#ddd",
            textstyle_opts=opts.TextStyleOpts(color="#333", font_size=12),
        ),
        legend_opts=opts.LegendOpts(is_show=False),
    )

    return map_chart


def generate_map_html(
    data_pairs: List[Tuple[str, float]],
    map_type: str,
    title: str,
    subtitle: str,
    range_colors: List[str],
    unit: str = "",
    show_labels: bool = True,
) -> str:
    """
    Generate a single static map and return HTML string.
    Used for single-year data.
    """
    vals = [v for _, v in data_pairs if v is not None]
    min_val = min(vals) if vals else 0
    max_val = max(vals) if vals else 100

    map_chart = _make_map(
        data_pairs=data_pairs,
        map_type=map_type,
        title=title,
        subtitle=subtitle,
        min_val=min_val,
        max_val=max_val,
        range_colors=range_colors,
        unit=unit,
        show_labels=show_labels,
    )

    return _render_chart_to_html(map_chart)


def generate_timeline_html(
    year_data_map: Dict[str, List[Tuple[str, float]]],
    map_type: str,
    title_template: str,
    subtitle: str,
    range_colors: List[str],
    unit: str = "",
    show_labels: bool = True,
    auto_play: bool = False,
    play_interval: int = 3000,
) -> str:
    """
    Generate a Timeline with multi-year data and return HTML string.

    Args:
        year_data_map: {year_label: [(region, value), ...]}
        title_template: Title template, use {year} placeholder
        subtitle: Subtitle text
        range_colors: Color scheme
        unit: Data unit label
        show_labels: Show region labels on map
        auto_play: Enable auto-play
        play_interval: Milliseconds between transitions
    """
    if not year_data_map:
        return "<p>No data to display</p>"

    years = sorted(year_data_map.keys())

    # Calculate global min/max for consistent color scale across years
    all_vals = []
    for pairs in year_data_map.values():
        for _, v in pairs:
            if v is not None:
                all_vals.append(v)
    global_min = min(all_vals) if all_vals else 0
    global_max = max(all_vals) if all_vals else 100

    sorted_colors = interpolate_light_dark(range_colors)

    tl = Timeline(
        init_opts=opts.InitOpts(
            width="1200px",
            height="700px",
            bg_color="#ffffff",
            animation_opts=opts.AnimationOpts(animation=True),
        )
    )
    tl.add_schema(
        is_auto_play=auto_play,
        play_interval=play_interval,
        pos_bottom="2%",
        width="85%",
        label_opts=opts.LabelOpts(font_size=12, color="#333"),
        is_loop_play=True,
    )

    for year in years:
        pairs = year_data_map[year]
        if "{year}" in title_template:
            title = title_template.replace("{year}", str(year))
        else:
            title = f"{year} {title_template}"

        if unit:
            year_subtitle = subtitle or f"数据来源：用户上传  单位：{unit}"
        else:
            year_subtitle = subtitle or "数据来源：用户上传"

        map_chart = _make_map(
            data_pairs=pairs,
            map_type=map_type,
            title=title,
            subtitle=year_subtitle,
            min_val=global_min,
            max_val=global_max,
            range_colors=sorted_colors,
            unit=unit,
            show_labels=show_labels,
        )

        tl.add(map_chart, str(year))

    return _render_chart_to_html(tl)


def generate_preview_html(
    year_data_map: Dict[str, List[Tuple[str, float]]],
    map_type: str,
    title_template: str,
    subtitle: str,
    range_colors: List[str],
    unit: str = "",
    show_labels: bool = True,
    auto_play: bool = False,
    play_interval: int = 3000,
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
    is_multi_year = len(years) > 1

    if is_multi_year:
        html = generate_timeline_html(
            year_data_map=year_data_map,
            map_type=map_type,
            title_template=title_template,
            subtitle=subtitle,
            range_colors=range_colors,
            unit=unit,
            show_labels=show_labels,
            auto_play=auto_play,
            play_interval=play_interval,
        )
    else:
        year = years[0]
        if "{year}" in title_template:
            title = title_template.replace("{year}", str(year))
        else:
            title = title_template
        html = generate_map_html(
            data_pairs=year_data_map[year],
            map_type=map_type,
            title=title,
            subtitle=subtitle,
            range_colors=range_colors,
            unit=unit,
            show_labels=show_labels,
        )

    return html, is_multi_year
