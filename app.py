"""
MapViz — Universal Data Map Visualization Tool
Drag/upload CSV → auto-detect country & year → interactive map
Streamlit Cloud ready
"""

import streamlit as st
import pandas as pd
from pyecharts.globals import CurrentConfig

from src.parser import parse_csv
from src.detector import detect_map_type
from src.matcher import match_all
from src.themes import get_theme, get_theme_list, validate_custom_colors
from src.generator import generate_preview_html

CurrentConfig.ONLINE_HOST = "https://assets.pyecharts.org/assets/v6/"

# ── Page config ──
st.set_page_config(
    page_title="MapViz - 数据地图可视化",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session-state init ──
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
    "title_template": "{year} 数据分布图",
    "subtitle": "",
    "unit": "",
    "show_labels": True,
    "auto_play": True,
    "play_interval": 3000,
    "html_content": "",
    "is_multi_year": False,
    "generated": False,
    "original_filename": "",
    "num_custom_colors": 6,
    "custom_color_values": ["#FF0000", "#FF6600", "#FFCC00", "#66CC00", "#0066CC", "#6600CC"],
}
for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ── Callback helpers ──
def _on_theme_preset_click(theme_key: str, colors: list):
    """Callback when user clicks a preset theme button."""
    st.session_state["theme_key"] = theme_key
    st.session_state["custom_colors"] = colors


def _on_generate_click():
    """Callback: user explicitly clicks 'Generate' — regenerate from scratch."""
    pass  # the button sets generation=True implicitly; just mark for freshness


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
    - 一列包含地区/国家名称
    - 其余列为各年份数据值
    - 支持任意表头位置（自动检测）
    """)

    st.markdown("---")
    st.markdown("#### 🗺️ 支持的地图")
    st.markdown("""
    - 🇨🇳 中国省份地图
    - 🌏 世界国家地图
    - 中/英文名称 + 模糊匹配
    """)

    st.markdown("---")
    st.caption("Made with ❤️ + Streamlit + pyecharts")


# ── Main area ──
st.title("🌍 MapViz — 通用数据地图可视化工具")
st.markdown("*上传CSV → 自动识别 → 一键生成交互式地图*")

# ═══════════════════════════════════════
# STEP 1 — File upload
# ═══════════════════════════════════════
st.markdown("---")
st.markdown("### 📂 Step 1: 上传数据文件")

uploaded_file = st.file_uploader(
    "拖拽或点击上传 CSV 文件",
    type=["csv"],
    help="支持 CSV 格式，自动检测编码和表头位置",
    key="file_uploader",
)

if uploaded_file is not None:
    st.session_state["file_bytes"] = uploaded_file.read()
    st.session_state["original_filename"] = uploaded_file.name
    st.session_state["generated"] = False
    st.session_state["manual_overrides"] = {}
    st.session_state["matched"] = {}
    st.session_state["uncertain"] = []

file_bytes = st.session_state.get("file_bytes")
if file_bytes is None:
    # ── No file yet — show help ──
    st.info("👆 请先上传 CSV 数据文件开始使用")
    st.markdown("---")
    st.markdown("### 📋 示例 CSV 格式")
    st.markdown("""
    工具会**自动跳过元数据行**找到真正的表头。例如以下文件：

    > 数据库：水资源统计
    > 数据来源：国家统计局
    > 地区,2023年,2022年,2021年
    > 北京市,41.5,23.7,61.3
    > 河北省,247.9,241.4,188.0

    前两行元数据会被自动跳过，直接识别第3行作为表头。
    支持中文和英文地区名，工具会自动翻译匹配。
    """)
    st.stop()

# ── Parse CSV ──
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

    st.success(
        f"✅ 文件解析成功 | 编码: **{encoding}** | "
        f"地区列: **{region_col}** | 数据列: **{len(year_cols)}** 个"
    )
    st.caption(
        f"文件名: {st.session_state['original_filename']} "
        f"| 大小: {len(file_bytes)/1024:.1f} KB"
    )
except Exception as e:
    st.error(f"❌ 文件解析失败: {e}")
    import traceback
    st.code(traceback.format_exc())
    st.stop()

# Show data preview
with st.expander("📊 数据预览（点击展开）", expanded=False):
    st.dataframe(df.head(20), use_container_width=True)
    st.caption(f"共 {len(df)} 行数据")

# ═══════════════════════════════════════
# STEP 2 — Map detection & name matching
# ═══════════════════════════════════════
st.markdown("---")
st.markdown("### 🔍 Step 2: 地图检测与名称匹配")

region_names = [str(n).strip() for n in df[region_col].dropna().tolist() if str(n).strip()]

map_type, map_label, confidence = detect_map_type(region_names)
st.session_state["map_type"] = map_type
st.session_state["map_label"] = map_label
st.session_state["confidence"] = confidence

col_a, col_b, col_c = st.columns(3)
col_a.metric("检测到地图类型", map_label)
col_b.metric("地区数量", len(region_names))
col_c.metric("匹配置信度", f"{confidence:.0%}")

matched, uncertain = match_all(region_names, map_type)
st.session_state["matched"] = matched
st.session_state["uncertain"] = uncertain

# Apply manual overrides the user previously confirmed
for orig, override in st.session_state["manual_overrides"].items():
    if orig in matched:
        matched[orig] = override

if uncertain:
    st.warning(f"⚠️ 有 {len(uncertain)} 个地区名称匹配置信度较低，请确认或修正：")
    with st.expander("🔧 修正名称匹配（点击展开）", expanded=True):
        st.caption("以下地名匹配不够精确，请从下拉列表中选择正确名称。")
        for i, item in enumerate(uncertain):
            orig = item["original"]
            conf_val = item["confidence"]
            alts = item["alternatives"]

            alt_display = [f"{name} ({score:.0f}%)" for name, score in alts[:5]]
            options = (
                [f"✅ 当前: {item['suggested']} ({conf_val:.0f}%)"]
                + alt_display
                + ["⏭️ 跳过（不在地图上显示）"]
            )

            c1, c2, c3 = st.columns([3, 1, 2])
            c1.text(f"原始: {orig}")
            c2.text(f"置信度: {conf_val:.0f}%")
            choice = c3.selectbox(
                "选择正确名称 →", options,
                key=f"fix_{i}",
                index=0,
            )

            if choice.startswith("✅ 当前:"):
                st.session_state["manual_overrides"][orig] = item["suggested"]
            elif choice.startswith("⏭️"):
                st.session_state["manual_overrides"][orig] = None
            else:
                name = choice.split(" (")[0] if " (" in choice else choice
                st.session_state["manual_overrides"][orig] = name

        if st.button("✅ 确认所有匹配", type="primary", key="confirm_matches"):
            for orig, override in st.session_state["manual_overrides"].items():
                if override is None:
                    matched.pop(orig, None)
                else:
                    matched[orig] = override
            st.session_state["matched"] = matched
            st.session_state["uncertain"] = []
            st.rerun()
else:
    st.success(f"✅ 所有 **{len(region_names)}** 个地区名称匹配成功！")

with st.expander("📋 查看所有匹配结果", expanded=False):
    match_df = pd.DataFrame(
        [(orig, std) for orig, std in matched.items()],
        columns=["原始名称", "映射后名称"],
    )
    st.dataframe(match_df, use_container_width=True, hide_index=True)

# ═══════════════════════════════════════
# STEP 3 — Configuration
# ═══════════════════════════════════════
st.markdown("---")
st.markdown("### ⚙️ Step 3: 配置地图")

# -- Title / subtitle --
c1, c2 = st.columns(2)
with c1:
    title_template = st.text_input(
        "地图标题（{year} = 年份占位符）",
        value=st.session_state["title_template"],
        help="使用 {year} 作为年份占位符",
        key="cfg_title",
    )
    st.session_state["title_template"] = title_template or "{year} 数据分布图"
with c2:
    subtitle = st.text_input(
        "副标题（可选）",
        value=st.session_state["subtitle"],
        placeholder="例：数据来源：国家统计局",
        key="cfg_subtitle",
    )
    st.session_state["subtitle"] = subtitle

c3, c4 = st.columns(2)
with c3:
    unit = st.text_input(
        "数据单位（可选）",
        value=st.session_state["unit"],
        placeholder="例：亿立方米、万人、%",
        key="cfg_unit",
    )
    st.session_state["unit"] = unit
with c4:
    show_labels = st.checkbox(
        "在地图上显示地区名称",
        value=st.session_state["show_labels"],
        help="勾选后每个区域上会显示文字标签",
        key="cfg_labels",
    )
    st.session_state["show_labels"] = show_labels

# -- Auto-play (multi-year only) --
if len(year_cols) > 1:
    st.session_state["is_multi_year"] = True
    pc1, pc2 = st.columns(2)
    with pc1:
        auto_play = st.checkbox(
            "⏯️ 自动播放年份",
            value=st.session_state["auto_play"],
            help="勾选后地图会自动切换年份",
            key="cfg_autoplay",
        )
        st.session_state["auto_play"] = auto_play
    with pc2:
        play_interval = st.slider(
            "播放间隔（毫秒）",
            1000, 10000, st.session_state["play_interval"], 500,
            key="cfg_interval",
        )
        st.session_state["play_interval"] = play_interval
else:
    st.session_state["is_multi_year"] = False
    st.session_state["auto_play"] = False

# -- Colour theme --
st.markdown("#### 🎨 颜色主题")

themes_list = get_theme_list()

tab_preset, tab_custom = st.tabs(["预设主题", "自定义颜色"])

with tab_preset:
    preset_cols = st.columns(5)
    for i, theme in enumerate(themes_list):
        with preset_cols[i % 5]:
            is_active = st.session_state["theme_key"] == theme["key"]
            border = "2px solid #1a73e8" if is_active else "1px solid #ddd"

            # Colour swatches
            swatch = "".join(
                f'<span style="display:inline-block;width:18px;height:18px;'
                f'background:{c};margin:1px;border-radius:2px;"></span>'
                for c in theme["colors"]
            )

            st.markdown(
                f'<div style="padding:8px;border:{border};border-radius:8px;margin:4px 0;">'
                f'<div style="font-weight:bold;font-size:13px;">{theme["name"]}</div>'
                f'<div style="font-size:11px;color:#888;">{theme["name_en"]}</div>'
                f'<div style="margin-top:4px;">{swatch}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            st.button(
                f"选择 {theme['name']}",
                key=f"theme_btn_{theme['key']}",
                use_container_width=True,
                on_click=_on_theme_preset_click,
                args=(theme["key"], theme["colors"]),
            )

with tab_custom:
    st.caption("自定义颜色渐变（从浅到深，至少2种颜色）")

    num_custom = st.number_input(
        "颜色数量", min_value=2, max_value=10,
        value=st.session_state.get("num_custom_colors", 6),
        key="num_custom_input",
    )
    st.session_state["num_custom_colors"] = num_custom

    cc_current = st.session_state.get("custom_colors", ["#E3F2FD", "#90CAF9", "#42A5F5", "#1E88E5", "#1565C0", "#0D47A1"])

    new_custom = []
    cc_cols = st.columns(num_custom)
    for i in range(num_custom):
        with cc_cols[i]:
            default_c = cc_current[i] if i < len(cc_current) else "#808080"
            c = st.color_picker(
                f"颜色 {i+1}",
                value=default_c,
                key=f"custom_picker_{i}",
            )
            new_custom.append(c)

    # Only commit custom if user is interacting with this tab
    # (prevent overwriting preset selection)
    if any(
        st.session_state.get(f"custom_picker_{i}") != (
            cc_current[i] if i < len(cc_current) else "#808080"
        )
        for i in range(num_custom)
    ):
        st.session_state["custom_colors"] = new_custom
        st.session_state["theme_key"] = "custom"

    # Preview gradient
    preview = (
        '<div style="display:flex;height:30px;border-radius:6px;overflow:hidden;margin-top:8px;">'
        + "".join(f'<div style="flex:1;background:{c};"></div>' for c in new_custom)
        + "</div>"
    )
    st.markdown(preview, unsafe_allow_html=True)

    if st.button("应用自定义颜色", key="apply_custom", use_container_width=True):
        st.session_state["custom_colors"] = new_custom
        st.session_state["theme_key"] = "custom"
        st.success("✅ 自定义颜色已保存，请点击下方「生成」按钮查看效果")

# ═══════════════════════════════════════
# STEP 4 — Generate
# ═══════════════════════════════════════
st.markdown("---")
st.markdown("### 🗺️ Step 4: 生成地图")

gen_col1, _ = st.columns([2, 1])
with gen_col1:
    generate_btn = st.button(
        "🚀 生成可视化地图",
        type="primary",
        use_container_width=True,
        key="generate_btn",
    )

# Build final matched dict
final_matched = dict(matched)
for orig, override in st.session_state.get("manual_overrides", {}).items():
    if override is None:
        final_matched.pop(orig, None)
    else:
        final_matched[orig] = override

if generate_btn or st.session_state.get("generated"):
    if generate_btn:
        st.session_state["generated"] = True

    with st.spinner("正在生成地图..."):
        try:
            # ── Build year data ──
            year_data_map = {}
            rc = st.session_state["region_col"]

            for yc in year_cols:
                ylabel = str(yc).strip()
                pairs = []
                for _, row in df.iterrows():
                    raw = str(row[rc]).strip()
                    std = final_matched.get(raw)
                    if std is None:
                        continue
                    try:
                        val = float(str(row[yc]).replace(",", "").replace("%", ""))
                    except (ValueError, TypeError):
                        continue
                    pairs.append((std, val))
                if pairs:
                    year_data_map[ylabel] = pairs

            if not year_data_map:
                st.error("没有有效数据，请检查数据格式和名称匹配。")
                st.stop()

            # ── Resolve colours ──
            theme_key = st.session_state["theme_key"]
            if theme_key == "custom":
                colors = validate_custom_colors(
                    st.session_state.get("custom_colors", [])
                )
            else:
                colors = get_theme(theme_key)["colors"]

            # ── Generate ──
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

            # ── Display ──
            st.markdown("#### 📊 地图预览")
            st.components.v1.html(html, height=800, scrolling=True)
            st.caption("💡 可缩放、悬停查看数值。如有问题可下载HTML文件在浏览器中打开。")

            # Info
            ci1, ci2, ci3, ci4 = st.columns(4)
            ci1.metric("地图类型", st.session_state["map_label"])
            ci2.metric("数据年份数", len(year_data_map))
            ci3.metric("颜色主题", theme_key)
            ci4.metric("展示模式", "🎬 多年度播放" if is_multi else "📷 单年度静态")

            # Download
            st.markdown("#### 📥 下载地图")
            st.caption("下载为独立 HTML 文件，可直接在浏览器中打开。")

            dl_name = (
                st.session_state["original_filename"]
                .replace(".csv", "").replace(".CSV", "")
            ) + "_map.html"

            st.download_button(
                label="💾 下载 HTML 地图文件",
                data=html,
                file_name=dl_name,
                mime="text/html",
                type="primary",
            )

        except Exception as e:
            st.error(f"❌ 生成地图时出错: {e}")
            import traceback
            st.code(traceback.format_exc())

# ── Footer ──
st.markdown("---")
st.caption("MapViz | Built with Streamlit + pyecharts | Deploy on Streamlit Cloud")
