"""
pyecharts map generator.
Supports single-year maps and multi-year Timeline with auto-play.
"""

from typing import List, Dict, Optional, Tuple
from pyecharts.charts import Map, Timeline
from pyecharts import options as opts

from .themes import interpolate_light_dark, get_theme


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
    tooltip_fmt = "{b}<br/>" + title + "：{c} " + unit if unit else "{b}<br/>" + title + "：{c}"

    # Sort colors so lighter comes first (for VisualMap)
    sorted_colors = interpolate_light_dark(range_colors)

    map_chart = Map()
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

    # Render to HTML string
    # pyecharts renders self-contained HTML
    return map_chart.render_embed()


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
            width="100%",
            height="650px",
            bg_color="#ffffff",
        )
    )
    tl.add_schema(
        is_auto_play=auto_play,
        play_interval=play_interval,
        pos_bottom="2%",
        width="80%",
        label_opts=opts.LabelOpts(font_size=12, color="#333"),
        is_loop_play=True,
    )

    for year in years:
        pairs = year_data_map[year]
        title = title_template.replace("{year}", str(year)) if "{year}" in title_template else f"{year} {title_template}"

        year_subtitle = subtitle or f"数据来源：用户上传  单位：{unit}" if unit else "数据来源：用户上传"

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

    return tl.render_embed()


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
        return "<p style='text-align:center;padding:40px;color:#999;'>请上传CSV数据文件</p>", False

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
        title = title_template.replace("{year}", str(year)) if "{year}" in title_template else title_template
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
