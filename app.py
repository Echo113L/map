"""
MapViz — Universal Data Map Visualization Tool
Drag/upload CSV → auto-detect country & year → interactive map
Streamlit Cloud ready
"""

import streamlit as st
import pandas as pd
import tempfile
import os
from io import BytesIO

from src.parser import parse_csv
from src.detector import detect_map_type
from src.matcher import match_all, get_alternatives
from src.themes import get_theme, get_theme_list, validate_custom_colors
from src.generator import generate_preview_html

# ── Page config ──
st.set_page_config(
    page_title="MapViz - 数据地图可视化",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Initialize session state ──
DEFAULTS = {
    "file_bytes": None,
    "df": None,
    "region_col": None,
    "year_cols": [],
    "map_type": "world",
    "map_label": "",
    "confidence": 0.0,
    "matched": {},
    "uncertain": [],
    "manual_overrides": {},
    "theme_key": "ocean_blue",
    "custom_colors": ["#E3F2FD", "#90CAF9", "#42A5F5", "#1E88E5", "#1565C0", "#0D47A1"],
    "title_template": "{year}全国水资源总量分布图",
    "subtitle": "",
    "unit": "",
    "show_labels": True,
    "auto_play": True,
    "play_interval": 3000,
    "html_content": "",
    "is_multi_year": False,
    "generated": False,
    "original_filename": "",
}
for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ── Sidebar ──
with st.sidebar:
    st.markdown("## 🌍 MapViz")
    st.markdown("### 通用数据地图可视化")
    st.markdown("---")

    st.markdown("#### 📖 使用步骤")
    st.markdown("""
    1. **上传** CSV 数据文件
    2. **确认** 地图类型和名称匹配
    3. **选择** 颜色主题
    4. **生成** 可视化地图
    5. **下载** HTML 文件
    """)

    st.markdown("---")
    st.markdown("#### 📋 CSV 格式要求")
    st.markdown("""
    - 第一列：地区/国家名称
    - 其余列：各年份的数据值
    - 支持中文/英文名称
    """)

    st.markdown("---")
    st.markdown("#### 🗺️ 支持的地图")
    st.markdown("""
    - 🇨🇳 中国省份地图
    - 🌏 世界国家地图
    - 支持多语言自动翻译
    """)

    st.markdown("---")
    st.caption("Made with ❤️ + Streamlit + pyecharts")


# ── Main area ──
st.title("🌍 MapViz — 通用数据地图可视化工具")
st.markdown("*上传CSV → 自动识别 → 一键生成交互式地图*")

# ═══════════════════════════════════════
# Step 1: File Upload
# ═══════════════════════════════════════
st.markdown("---")
st.markdown("### 📂 Step 1: 上传数据文件")

uploaded_file = st.file_uploader(
    "拖拽或点击上传 CSV 文件",
    type=["csv"],
    help="支持 CSV 格式，自动检测编码（UTF-8, GBK, GB2312 等）",
    key="file_uploader",
)

if uploaded_file is not None:
    # New file uploaded — persist in session state
    st.session_state["file_bytes"] = uploaded_file.read()
    st.session_state["original_filename"] = uploaded_file.name
    st.session_state["generated"] = False
    st.session_state["manual_overrides"] = {}
    st.session_state["matched"] = {}
    st.session_state["uncertain"] = []

# Process from session state (survives reruns)
file_bytes = st.session_state.get("file_bytes")
if file_bytes is not None:

    # Parse CSV
    try:
        df, encoding, region_col, year_cols = parse_csv(file_bytes)

        if region_col is None:
            st.error("❌ 无法识别地区名称列，请确保 CSV 中有一列包含地区/国家名称。")
            st.stop()

        if not year_cols:
            st.error("❌ 未检测到数据列，请确保 CSV 中包含数值数据列。")
            st.stop()

        st.session_state["df"] = df
        st.session_state["region_col"] = region_col
        st.session_state["year_cols"] = year_cols

        st.success(f"✅ 文件解析成功 | 编码: {encoding} | 地区列: **{region_col}** | 数据列: {len(year_cols)} 个")
        st.caption(f"文件名: {st.session_state['original_filename']} | 大小: {len(file_bytes)/1024:.1f} KB")

    except Exception as e:
        st.error(f"❌ 文件解析失败: {e}")
        st.stop()

    # Show data preview
    with st.expander("📊 数据预览（点击展开）", expanded=False):
        st.dataframe(df.head(20), use_container_width=True)
        st.caption(f"共 {len(df)} 行数据")

    # ═══════════════════════════════════════
    # Step 2: Map Detection & Name Matching
    # ═══════════════════════════════════════
    st.markdown("---")
    st.markdown("### 🔍 Step 2: 地图检测与名称匹配")

    region_names = df[region_col].dropna().tolist()
    region_names = [str(n).strip() for n in region_names if str(n).strip()]

    map_type, map_label, confidence = detect_map_type(region_names)
    st.session_state["map_type"] = map_type
    st.session_state["map_label"] = map_label
    st.session_state["confidence"] = confidence

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("检测到地图类型", map_label)
    with col_b:
        st.metric("地区数量", len(region_names))
    with col_c:
        st.metric("匹配置信度", f"{confidence:.0%}")

    # Run matcher
    matched, uncertain = match_all(region_names, map_type)
    st.session_state["matched"] = matched
    st.session_state["uncertain"] = uncertain

    # Apply manual overrides
    for orig, override in st.session_state["manual_overrides"].items():
        if orig in matched:
            matched[orig] = override

    if uncertain:
        st.warning(f"⚠️ 有 {len(uncertain)} 个地区名称匹配置信度较低，请确认或修正：")

        with st.expander("🔧 修正名称匹配（点击展开）", expanded=True):
            st.caption("以下地名匹配不够精确，请从下拉列表中选择正确名称，或直接输入。")

            for i, item in enumerate(uncertain):
                orig = item["original"]
                confidence_val = item["confidence"]
                alternatives = item["alternatives"]

                alt_display = [f"{name} ({score:.0f}%)" for name, score in alternatives[:5]]
                alt_values = [name for name, _ in alternatives[:5]]

                # Add current suggestion and "Skip" option
                options = [f"✅ 当前: {item['suggested']} ({confidence_val:.0f}%)"] + alt_display + ["⏭️ 跳过（不在地图上显示）"]

                cols = st.columns([3, 1, 2])
                with cols[0]:
                    st.text(f"原始名称: {orig}")
                with cols[1]:
                    st.text(f"置信度: {confidence_val:.0f}%")
                with cols[2]:
                    choice = st.selectbox(
                        f"选择正确名称 →",
                        options=options,
                        key=f"fix_{orig}_{i}",
                        index=0,
                    )

                if choice.startswith("✅ 当前:"):
                    # Keep the suggestion
                    st.session_state["manual_overrides"][orig] = item["suggested"]
                elif choice.startswith("⏭️"):
                    st.session_state["manual_overrides"][orig] = None  # Skip
                else:
                    # Extract name from display format
                    selected_name = choice.split(" (")[0] if " (" in choice else choice
                    st.session_state["manual_overrides"][orig] = selected_name

            # Apply button
            if st.button("✅ 确认所有匹配", type="primary", key="confirm_matches"):
                # Apply all manual overrides to matched dict
                for orig, override in st.session_state["manual_overrides"].items():
                    if override is None:
                        matched.pop(orig, None)
                    else:
                        matched[orig] = override
                st.session_state["matched"] = matched
                st.session_state["uncertain"] = []
                st.rerun()
    else:
        st.success(f"✅ 所有 {len(region_names)} 个地区名称匹配成功！")

    # Show match summary
    with st.expander("📋 查看所有匹配结果", expanded=False):
        match_df = pd.DataFrame(
            [(orig, std) for orig, std in matched.items()],
            columns=["原始名称", "映射后名称"],
        )
        st.dataframe(match_df, use_container_width=True, hide_index=True)

    # ═══════════════════════════════════════
    # Step 3: Configuration
    # ═══════════════════════════════════════
    st.markdown("---")
    st.markdown("### ⚙️ Step 3: 配置地图")

    # -- Title config --
    cfg_col1, cfg_col2 = st.columns(2)
    with cfg_col1:
        default_title = st.session_state["title_template"]
        if "{" not in default_title:
            # Ensure {year} placeholder exists
            default_title = "{year}" + default_title

        title_template = st.text_input(
            "地图标题（{year} 会被替换为实际年份）",
            value=default_title,
            help="使用 {year} 作为年份占位符",
        )
        st.session_state["title_template"] = title_template

    with cfg_col2:
        subtitle = st.text_input(
            "副标题（可选）",
            value=st.session_state["subtitle"],
            placeholder="例如：数据来源：国家统计局",
        )
        st.session_state["subtitle"] = subtitle

    unit_cfg, label_cfg = st.columns(2)
    with unit_cfg:
        unit = st.text_input(
            "数据单位（可选）",
            value=st.session_state["unit"],
            placeholder="例如：亿立方米、万人、%",
        )
        st.session_state["unit"] = unit

    with label_cfg:
        show_labels = st.checkbox(
            "在地图上显示地区名称",
            value=st.session_state["show_labels"],
            help="勾选后每个区域上会显示文字标签",
        )
        st.session_state["show_labels"] = show_labels

    # -- Auto-play config (only for multi-year) --
    if len(year_cols) > 1:
        st.session_state["is_multi_year"] = True
        play_col1, play_col2 = st.columns(2)
        with play_col1:
            auto_play = st.checkbox(
                "⏯️ 自动播放年份",
                value=st.session_state["auto_play"],
                help="勾选后地图会自动切换年份进行播放对比",
            )
            st.session_state["auto_play"] = auto_play
        with play_col2:
            play_interval = st.slider(
                "播放间隔（毫秒）",
                min_value=1000,
                max_value=10000,
                value=st.session_state["play_interval"],
                step=500,
                help="每个年份停留的时间",
            )
            st.session_state["play_interval"] = play_interval
    else:
        st.session_state["is_multi_year"] = False
        st.session_state["auto_play"] = False

    # -- Color theme --
    st.markdown("#### 🎨 颜色主题")

    themes_list = get_theme_list()

    theme_tabs = st.tabs(["预设主题", "自定义颜色"])

    with theme_tabs[0]:
        # Show preset themes as color swatches
        preset_cols = st.columns(5)
        for i, theme in enumerate(themes_list):
            col_idx = i % 5
            with preset_cols[col_idx]:
                # Draw color swatch
                swatch_html = ""
                for color in theme["colors"]:
                    swatch_html += f'<span style="display:inline-block;width:18px;height:18px;background:{color};margin:1px;border-radius:2px;"></span>'
                is_active = st.session_state["theme_key"] == theme["key"]
                border = "2px solid #1a73e8" if is_active else "1px solid #ddd"

                st.markdown(
                    f'<div style="padding:8px;border:{border};border-radius:8px;cursor:pointer;margin:4px 0;">'
                    f'<div style="font-weight:bold;font-size:13px;">{theme["name"]}</div>'
                    f'<div style="font-size:11px;color:#888;">{theme["name_en"]}</div>'
                    f'<div style="margin-top:4px;">{swatch_html}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                if st.button(f"选择 {theme['name']}", key=f"theme_btn_{theme['key']}", use_container_width=True):
                    st.session_state["theme_key"] = theme["key"]
                    st.session_state["custom_colors"] = theme["colors"]
                    st.rerun()

    with theme_tabs[1]:
        st.caption("自定义颜色渐变（从浅到深，至少需要2种颜色）")

        custom_colors = st.session_state.get("custom_colors", ["#E3F2FD", "#42A5F5", "#0D47A1"])
        num_custom = st.number_input("颜色数量", min_value=2, max_value=10, value=len(custom_colors), key="num_custom")

        new_custom = []
        color_cols = st.columns(num_custom)
        for i in range(num_custom):
            with color_cols[i]:
                default_color = custom_colors[i] if i < len(custom_colors) else "#808080"
                c = st.color_picker(f"颜色 {i+1}", value=default_color, key=f"custom_color_{i}")
                new_custom.append(c)

        st.session_state["custom_colors"] = new_custom
        st.session_state["theme_key"] = "custom"

        # Preview gradient
        preview_html = '<div style="display:flex;height:30px;border-radius:6px;overflow:hidden;margin-top:8px;">'
        for c in new_custom:
            preview_html += f'<div style="flex:1;background:{c};"></div>'
        preview_html += "</div>"
        st.markdown(preview_html, unsafe_allow_html=True)

    # ═══════════════════════════════════════
    # Step 4: Generate Map
    # ═══════════════════════════════════════
    st.markdown("---")
    st.markdown("### 🗺️ Step 4: 生成地图")

    gen_col1, gen_col2 = st.columns([2, 1])
    with gen_col1:
        generate_btn = st.button(
            "🚀 生成可视化地图",
            type="primary",
            use_container_width=True,
            key="generate_btn",
        )

    # Update matched dict with manual overrides before generation
    final_matched = dict(matched)
    for orig, override in st.session_state.get("manual_overrides", {}).items():
        if override is None:
            final_matched.pop(orig, None)
        else:
            final_matched[orig] = override

    if generate_btn or st.session_state.get("generated"):
        st.session_state["generated"] = True

        with st.spinner("正在生成地图..."):
            try:
                # Build data for each year
                year_data_map = {}
                region_col_name = st.session_state["region_col"]

                for year_col in year_cols:
                    year_label = str(year_col).strip()
                    data_pairs = []

                    for _, row in df.iterrows():
                        raw_name = str(row[region_col_name]).strip()
                        if not raw_name or raw_name.lower() == "nan":
                            continue

                        std_name = final_matched.get(raw_name)
                        if std_name is None:
                            continue

                        try:
                            val = float(row[year_col])
                        except (ValueError, TypeError):
                            continue

                        data_pairs.append((std_name, val))

                    if data_pairs:
                        year_data_map[year_label] = data_pairs

                if not year_data_map:
                    st.error("没有有效数据可生成地图，请检查数据格式和名称匹配。")
                    st.stop()

                # Get colors
                theme_key = st.session_state["theme_key"]
                if theme_key == "custom":
                    colors = validate_custom_colors(st.session_state.get("custom_colors", []))
                else:
                    colors = get_theme(theme_key)["colors"]

                # Generate HTML
                html, is_multi = generate_preview_html(
                    year_data_map=year_data_map,
                    map_type=st.session_state["map_type"],
                    title_template=st.session_state["title_template"],
                    subtitle=st.session_state["subtitle"],
                    range_colors=colors,
                    unit=st.session_state["unit"],
                    show_labels=st.session_state["show_labels"],
                    auto_play=st.session_state.get("auto_play", False),
                    play_interval=st.session_state.get("play_interval", 3000),
                )

                st.session_state["html_content"] = html
                st.session_state["is_multi_year"] = is_multi

                # Display the map
                st.markdown("#### 📊 地图预览")
                st.components.v1.html(html, height=700, scrolling=False)

                # Show info
                info_cols = st.columns(4)
                with info_cols[0]:
                    st.metric("地图类型", st.session_state["map_label"])
                with info_cols[1]:
                    st.metric("数据年份数", len(year_data_map))
                with info_cols[2]:
                    st.metric("颜色主题", theme_key)
                with info_cols[3]:
                    mode = "🎬 多年度播放" if is_multi else "📷 单年度静态"
                    st.metric("展示模式", mode)

                # Download button
                st.markdown("#### 📥 下载地图")
                st.caption("下载为独立的 HTML 文件，可直接在浏览器中打开查看交互式地图。")

                download_filename = (
                    st.session_state["original_filename"]
                    .replace(".csv", "")
                    .replace(".CSV", "")
                ) + "_map.html"

                st.download_button(
                    label="💾 下载 HTML 地图文件",
                    data=html,
                    file_name=download_filename,
                    mime="text/html",
                    type="primary",
                )

            except Exception as e:
                st.error(f"❌ 生成地图时出错: {e}")
                import traceback
                st.code(traceback.format_exc())

else:
    # No file uploaded — show demo
    st.info("👆 请先上传 CSV 数据文件开始使用")

    st.markdown("---")
    st.markdown("### 📋 示例 CSV 格式")
    st.markdown("""
    你的 CSV 文件应该类似这样：

    | 地区 | 2023年 | 2022年 | 2021年 |
    |------|--------|--------|--------|
    | 北京 | 41.5 | 23.7 | 61.3 |
    | 河北 | 247.9 | 241.4 | 188.0 |
    | 上海 | 53.4 | 41.5 | 33.1 |
    | ...  | ...    | ...    | ...    |

    支持中文和英文地区名，工具会自动翻译匹配。
    """)

    st.markdown("---")
    st.markdown("### 🎯 功能特色")
    feat_cols = st.columns(4)
    with feat_cols[0]:
        st.markdown("#### 🌐 多语言识别")
        st.markdown("自动识别中英文名称，智能翻译到pyecharts标准名")
    with feat_cols[1]:
        st.markdown("#### 🗺️ 自动检测")
        st.markdown("自动判断中国省份/世界国家，选择正确地图模板")
    with feat_cols[2]:
        st.markdown("#### 🎨 自定义配色")
        st.markdown("10种预设主题 + 完整的自定义颜色选择器")
    with feat_cols[3]:
        st.markdown("#### ⏱️ 年度播放")
        st.markdown("多年份数据自动生成Timeline，支持自动播放对比")


# ── Footer ──
st.markdown("---")
st.caption("MapViz | Built with Streamlit + pyecharts | Deploy on Streamlit Cloud")
