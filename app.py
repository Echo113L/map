"""
MapViz — Universal Data Map Visualization Tool
Upload CSV or enter data manually → auto-detect → interactive map
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

st.set_page_config(
    page_title="MapViz - 数据地图可视化",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session-state keys ──────────────────────────────────────────────────

def _init(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

_init("mode", "csv")
_init("file_bytes", None)
_init("df", None)
_init("region_col", None)
_init("year_cols", [])
_init("map_type", "world")
_init("map_label", "")
_init("confidence", 0.0)
_init("matched", {})
_init("uncertain", [])
_init("manual_overrides", {})
_init("theme_key", "ocean_blue")
_init("custom_colors", ["#E3F2FD", "#90CAF9", "#42A5F5", "#1E88E5", "#1565C0", "#0D47A1"])
_init("title_template", "{year} 数据分布图")
_init("subtitle", "")
_init("unit", "")
_init("show_labels", True)
_init("auto_play", True)
_init("play_interval", 3000)
_init("force_piecewise", False)
_init("html_content", "")
_init("is_multi_year", False)
_init("generated", False)
_init("original_filename", "")
_init("manual_region_names", ["Region1", "Region2", "Region3"])
_init("manual_values", [10.0, 50.0, 100.0])


# ── Sidebar ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🌍 MapViz")
    st.markdown("### 通用数据地图可视化")
    st.markdown("---")
    st.markdown("#### 📖 使用步骤")
    st.markdown("""
    1. **上传 CSV** 或 **手动输入** 数据
    2. **确认** 地图类型和名称匹配
    3. **选择** 颜色主题
    4. **生成** 可视化地图
    5. **下载** HTML 文件
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


# ── Header ──────────────────────────────────────────────────────────────

st.title("🌍 MapViz — 通用数据地图可视化工具")

# ── Mode selector ──
mode = st.radio(
    "选择数据输入方式",
    options=["csv", "manual"],
    index=0 if st.session_state["mode"] == "csv" else 1,
    format_func=lambda x: "📂 上传 CSV 文件" if x == "csv" else "✏️ 手动输入数据",
    horizontal=True,
    key="mode_radio",
)
st.session_state["mode"] = mode

st.markdown("---")


# ═══════════════════════════════════════════════════════════════
# MODE A — CSV upload
# ═══════════════════════════════════════════════════════════════

if mode == "csv":
    st.markdown("### 📂 Step 1: 上传数据文件")

    uploaded_file = st.file_uploader(
        "拖拽或点击上传 CSV 文件",
        type=["csv"],
        help="支持 CSV 格式，自动检测编码和表头位置",
        key="file_uploader",
    )

    if uploaded_file is not None:
        if st.session_state.get("_prev_filename") != uploaded_file.name:
            st.session_state["file_bytes"] = uploaded_file.read()
            st.session_state["original_filename"] = uploaded_file.name
            st.session_state["generated"] = False
            st.session_state["manual_overrides"] = {}
            st.session_state["matched"] = {}
            st.session_state["uncertain"] = []
            st.session_state["_prev_filename"] = uploaded_file.name

    file_bytes = st.session_state.get("file_bytes")

    if file_bytes is None:
        st.info("👆 请先上传 CSV 数据文件开始使用")
        st.markdown("---")
        st.markdown("### 📋 工具会自动跳过元数据行，找到真正的表头")
        st.markdown("""
        > 数据库：水资源统计 *(自动跳过)*
        > 数据来源：国家统计局 *(自动跳过)*
        > 地区,2023年,2022年,2021年 ← **真正的表头**
        > 北京市,41.5,23.7,61.3
        > 河北省,247.9,241.4,188.0
        """)
        st.stop()

    try:
        df, encoding, region_col, year_cols = parse_csv(file_bytes)
        if region_col is None:
            st.error("无法识别地区名称列，请确保 CSV 中有一列包含地区/国家名称。")
            st.stop()
        if not year_cols:
            st.error("未检测到数据列，请确保 CSV 中包含数值数据列。")
            st.stop()

        st.session_state["df"] = df
        st.session_state["region_col"] = region_col
        st.session_state["year_cols"] = year_cols

        st.success(
            f"文件解析成功 | 编码: **{encoding}** | "
            f"地区列: **{region_col}** | 数据列: **{len(year_cols)}** 个"
        )
        st.caption(f"文件名: {st.session_state['original_filename']} | 大小: {len(file_bytes)/1024:.1f} KB")
    except Exception as e:
        st.error(f"文件解析失败: {e}")
        import traceback
        st.code(traceback.format_exc())
        st.stop()

    with st.expander("📊 数据预览（点击展开）", expanded=False):
        st.dataframe(df.head(20), use_container_width=True)
        st.caption(f"共 {len(df)} 行数据")

    region_names = [str(n).strip() for n in df[region_col].dropna().tolist() if str(n).strip()]


# ═══════════════════════════════════════════════════════════════
# MODE B — Manual data entry
# ═══════════════════════════════════════════════════════════════

else:  # mode == "manual"
    st.markdown("### ✏️ Step 1: 手动输入数据")

    manual_map_type = st.selectbox(
        "选择地图类型",
        options=["china", "world"],
        index=0 if st.session_state.get("map_type", "china") == "china" else 1,
        format_func=lambda x: "🇨🇳 中国省份地图" if x == "china" else "🌏 世界国家地图",
        key="manual_map_type",
    )
    st.session_state["map_type"] = manual_map_type
    st.session_state["map_label"] = {
        "china": "中国地图 (China)", "world": "世界地图 (World)"
    }.get(manual_map_type, manual_map_type)

    st.caption("在表格中直接编辑地区名称和数值。可添加/删除行。")

    default_data = {
        "地区": st.session_state.get("manual_region_names", []),
        "值": st.session_state.get("manual_values", []),
    }
    n = max(len(default_data["地区"]), len(default_data["值"]))
    while len(default_data["地区"]) < n:
        default_data["地区"].append("")
    while len(default_data["值"]) < n:
        default_data["值"].append(0.0)

    manual_df = pd.DataFrame(default_data)
    edited_df = st.data_editor(
        manual_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "地区": st.column_config.TextColumn("地区/国家名称", width="large"),
            "值": st.column_config.NumberColumn("数值", format="%.4f"),
        },
        key="manual_data_editor",
    )

    st.session_state["manual_region_names"] = edited_df["地区"].tolist()
    st.session_state["manual_values"] = edited_df["值"].tolist()

    clean_regions = [str(r).strip() for r in edited_df["地区"].tolist() if str(r).strip()]
    clean_vals = []
    for r, v in zip(edited_df["地区"].tolist(), edited_df["值"].tolist()):
        if str(r).strip():
            try:
                clean_vals.append(float(v))
            except (ValueError, TypeError):
                clean_vals.append(0.0)

    if len(clean_regions) < 2:
        st.warning("请至少输入 2 个地区及其数值。")
        st.stop()

    df = pd.DataFrame({"地区": clean_regions, "值": clean_vals})
    region_col = "地区"
    year_cols = ["值"]

    st.session_state["df"] = df
    st.session_state["region_col"] = region_col
    st.session_state["year_cols"] = year_cols
    st.session_state["manual_overrides"] = {}
    st.session_state["is_multi_year"] = False
    st.session_state["auto_play"] = False

    region_names = clean_regions

    st.caption(f"已输入 **{len(clean_regions)}** 个地区，数值范围: "
               f"{min(clean_vals):.2f} - {max(clean_vals):.2f}")


# ═══════════════════════════════════════════════════════════════
# STEP 2 — Map detection & name matching
# ═══════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("### 🔍 Step 2: 地图检测与名称匹配")

if mode == "csv":
    map_type, map_label, confidence = detect_map_type(region_names)
    st.session_state["map_type"] = map_type
    st.session_state["map_label"] = map_label
    st.session_state["confidence"] = confidence
else:
    map_type = st.session_state["map_type"]
    map_label = st.session_state["map_label"]
    confidence = 1.0
    st.session_state["confidence"] = 1.0

col_a, col_b, col_c = st.columns(3)
col_a.metric("地图类型", map_label)
col_b.metric("地区数量", len(region_names))
col_c.metric("匹配置信度", f"{confidence:.0%}")

matched, uncertain = match_all(region_names, map_type)
st.session_state["matched"] = matched
st.session_state["uncertain"] = uncertain

for orig, override in st.session_state["manual_overrides"].items():
    if orig in matched:
        matched[orig] = override

if uncertain:
    st.warning(f"有 {len(uncertain)} 个地区名称需要确认：")
    with st.expander("🔧 修正名称匹配（点击展开）", expanded=True):
        for i, item in enumerate(uncertain):
            alts = item["alternatives"]
            alt_display = [f"{n} ({s:.0f}%)" for n, s in alts[:5]]
            options = (
                [f"当前: {item['suggested']} ({item['confidence']:.0f}%)"]
                + alt_display
                + ["跳过（不在地图上显示）"]
            )
            c1, c2, c3 = st.columns([3, 1, 2])
            c1.text(f"原始: {item['original']}")
            c2.text(f"置信度: {item['confidence']:.0f}%")
            choice = c3.selectbox("选择正确名称 →", options, key=f"fix_{i}", index=0)
            if choice.startswith("跳过"):
                st.session_state["manual_overrides"][item["original"]] = None
            elif "当前" not in choice:
                name = choice.split(" (")[0] if " (" in choice else choice
                st.session_state["manual_overrides"][item["original"]] = name
            else:
                st.session_state["manual_overrides"][item["original"]] = item["suggested"]

        if st.button("确认所有匹配", type="primary", key="confirm_matches"):
            for orig, override in st.session_state["manual_overrides"].items():
                if override is None:
                    matched.pop(orig, None)
                else:
                    matched[orig] = override
            st.session_state["matched"] = matched
            st.session_state["uncertain"] = []
            st.rerun()
else:
    st.success(f"所有 **{len(region_names)}** 个地区名称匹配成功！")

with st.expander("📋 匹配结果详情", expanded=False):
    match_df = pd.DataFrame(
        [(orig, std) for orig, std in matched.items()],
        columns=["原始名称", "映射后名称"],
    )
    st.dataframe(match_df, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════
# STEP 3 — Configuration
# ═══════════════════════════════════════════════════════════════

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

# -- Auto-play --
if mode == "csv" and len(st.session_state.get("year_cols", [])) > 1:
    st.session_state["is_multi_year"] = True
    pc1, pc2 = st.columns(2)
    with pc1:
        auto_play = st.checkbox(
            "自动播放年份",
            value=st.session_state["auto_play"],
            key="cfg_autoplay",
        )
        st.session_state["auto_play"] = auto_play
    with pc2:
        st.session_state["play_interval"] = st.slider(
            "播放间隔（毫秒）", 1000, 10000,
            st.session_state["play_interval"], 500,
            key="cfg_interval",
        )
elif mode == "manual":
    st.session_state["is_multi_year"] = False
    st.session_state["auto_play"] = False
else:
    st.session_state["is_multi_year"] = False
    st.session_state["auto_play"] = False

# -- Colour theme + piecewise toggle ─────────────────────────
st.markdown("#### 🎨 颜色主题")

themes_list = get_theme_list()
current_theme_key = st.session_state["theme_key"]

# Piecewise toggle
st.checkbox(
    "分段图例模式 — 适合数值差异微小的情况，每个颜色块有明确边界",
    value=st.session_state.get("force_piecewise", False),
    key="cfg_force_piecewise",
)
st.session_state["force_piecewise"] = st.session_state["cfg_force_piecewise"]

# ── 2×4 preset swatch grid ──
st.caption("**预设配色** — 点击色块选择")

for row in range(2):
    cols = st.columns(4)
    for col_i in range(4):
        idx = row * 4 + col_i
        if idx >= len(themes_list):
            break
        theme = themes_list[idx]
        with cols[col_i]:
            is_active = current_theme_key == theme["key"]
            border = "3px solid #1a73e8" if is_active else "1px solid #ddd"
            bg = "#e8f0fe" if is_active else "#fff"

            swatch = "".join(
                f'<span style="display:inline-block;width:16px;height:16px;'
                f'background:{c};margin:1px;border-radius:2px;"></span>'
                for c in theme["colors"]
            )

            st.markdown(
                f'<div style="border:{border};border-radius:10px;padding:10px 8px;'
                f'background:{bg};text-align:center;margin:2px 0;">'
                f'<div style="font-weight:bold;font-size:13px;">{theme["name"]}</div>'
                f'<div style="font-size:10px;color:#888;margin-bottom:4px;">{theme["name_en"]}</div>'
                f'<div style="margin:4px 0;">{swatch}</div>'
                f'<div style="font-size:10px;color:#666;">{theme["description"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            label = f"{'⭐ ' if is_active else ''}{theme['name']}"
            if st.button(label, key=f"theme_btn_{theme['key']}", use_container_width=True):
                st.session_state["theme_key"] = theme["key"]
                st.session_state["custom_colors"] = theme["colors"]
                st.rerun()

st.markdown("---")

# ── Chromatic spectrum (custom colour picker row) ──
st.caption("**自定义色谱** — 调整颜色后点击「应用自定义颜色」")

num_custom = st.number_input(
    "颜色节点数", min_value=2, max_value=10,
    value=len(st.session_state.get("custom_colors", get_theme("ocean_blue")["colors"])),
    key="num_custom_colors",
)
current_custom = st.session_state.get("custom_colors", get_theme("ocean_blue")["colors"])
new_custom = []
cc_cols = st.columns(num_custom)
for i in range(num_custom):
    with cc_cols[i]:
        default_c = current_custom[i] if i < len(current_custom) else "#808080"
        label = "最浅" if i == 0 else ("最深" if i == num_custom - 1 else f"#{i+1}")
        c = st.color_picker(label, value=default_c, key=f"custom_picker_v3_{i}")
        new_custom.append(c)

# Preview gradient bar
preview = (
    '<div style="display:flex;height:36px;border-radius:6px;overflow:hidden;margin:8px 0;">'
    + "".join(f'<div style="flex:1;background:{c};"></div>' for c in new_custom)
    + "</div>"
)
st.markdown(preview, unsafe_allow_html=True)

if st.button("应用自定义颜色", key="apply_custom_v3", use_container_width=True, type="primary"):
    validated = validate_custom_colors(new_custom)
    st.session_state["custom_colors"] = validated
    st.session_state["theme_key"] = "custom"
    st.success("✅ 自定义颜色已保存，请点击下方「生成」按钮查看效果")


# ═══════════════════════════════════════════════════════════════
# STEP 4 — Generate
# ═══════════════════════════════════════════════════════════════

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

if generate_btn:
    st.session_state["generated"] = True

if st.session_state.get("generated"):
    with st.spinner("正在生成地图..."):
        try:
            # Build year data
            year_data_map = {}
            rc = st.session_state["region_col"]
            year_cols = st.session_state.get("year_cols", [])

            for yc in year_cols:
                ylabel = str(yc).strip()
                pairs = []
                for _, row in st.session_state["df"].iterrows():
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

            # Resolve colours
            theme_key = st.session_state["theme_key"]
            if theme_key == "custom":
                colors = validate_custom_colors(
                    st.session_state.get("custom_colors", [])
                )
            else:
                colors = get_theme(theme_key)["colors"]

            # Generate
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
                force_piecewise=st.session_state.get("force_piecewise", False),
            )

            st.session_state["html_content"] = html
            st.session_state["is_multi_year"] = is_multi

            # Display
            st.markdown("#### 📊 地图预览")
            st.components.v1.html(html, height=800, scrolling=True)
            st.caption("💡 可缩放、悬停查看数值。如有问题可下载 HTML 文件在浏览器中打开。")

            # Info
            ci1, ci2, ci3, ci4 = st.columns(4)
            ci1.metric("地图类型", st.session_state["map_label"])
            ci2.metric("数据年份数", len(year_data_map))
            ci3.metric("颜色主题", theme_key)
            ci4.metric("展示模式",
                       "🎬 Timeline 播放" if is_multi else "📷 静态地图")

            # Download
            st.markdown("#### 📥 下载地图")
            st.caption("下载为独立 HTML 文件，可直接在浏览器中打开。")
            dl_name = (
                st.session_state.get("original_filename", "data")
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
            st.error(f"生成地图时出错: {e}")
            import traceback
            st.code(traceback.format_exc())

# ── Footer ──
st.markdown("---")
st.caption("MapViz | Built with Streamlit + pyecharts | Deploy on Streamlit Cloud")
