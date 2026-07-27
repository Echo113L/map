# 🌍 MapViz — 通用数据地图可视化工具

拖拽上传 CSV 数据文件，自动识别国家/地区、年份，一键生成交互式数据地图。

## ✨ 功能特色

- **🌐 多语言自动翻译** — 支持中英文地区名称，自动映射到 pyecharts 标准地图名称
- **🗺️ 智能地图检测** — 自动识别中国省份/世界国家，匹配正确的 pyecharts 地图模板
- **🎨 自定义配色** — 10 种预设颜色主题 + 完整的自定义颜色选择器
- **⏱️ 年度对比播放** — 多年份数据自动生成 Timeline，支持自动播放
- **🔧 模糊匹配修正** — 名称为模糊匹配时，用户可从候选中手动确认
- **📥 一键下载** — 生成独立的交互式 HTML 文件，可在浏览器中直接打开

## 🚀 在线使用

> 部署到 **Streamlit Cloud** 后，任何人都可以通过链接使用。

### 部署步骤

1. Fork 或上传本仓库到你的 GitHub
2. 前往 [Streamlit Cloud](https://streamlit.io/cloud) 登录
3. 点击 "New app"，选择本仓库，主文件路径填写 `app.py`
4. 点击 "Deploy"，等待部署完成

部署完成后你会获得一个公开链接，分享给其他人即可。

## 💻 本地运行

### 环境要求

- Python 3.9+
- pip

### 安装

```bash
cd mapviz_tool
pip install -r requirements.txt
```

### 运行

```bash
streamlit run app.py
```

浏览器会自动打开 `http://localhost:8501`。

## 📋 数据格式

上传的 CSV 文件需要满足以下格式：

| 地区 | 2023年 | 2022年 | 2021年 |
|------|--------|--------|--------|
| 北京 | 41.5 | 23.7 | 61.3 |
| 河北 | 247.9 | 241.4 | 188.0 |
| 上海 | 53.4 | 41.5 | 33.1 |
| ... | ... | ... | ... |

- **第一列**：地区/国家名称（中文或英文均可）
- **其余列**：各年份的数据值
- 支持 UTF-8、GBK、GB2312 等常见编码

### 中国省份数据

支持以下名称格式（任意一种均可自动识别）：
- `北京`、`北京市`、`Beijing`、`Peking`
- `河北`、`河北省`、`Hebei`
- `内蒙古`、`内蒙古自治区`、`Inner Mongolia`
- ... 等等

### 世界国家数据

支持以下名称格式：
- 中文：`中国`、`美国`、`日本` ...
- 英文：`China`、`United States`、`Japan` ...
- 简写：`USA`、`UK`、`UAE` ...

## 📁 项目结构

```
mapviz_tool/
├── app.py                  # Streamlit 主应用
├── requirements.txt        # Python 依赖
├── README.md               # 使用文档
├── .streamlit/
│   └── config.toml         # Streamlit 配置
└── src/
    ├── __init__.py
    ├── parser.py           # CSV 智能解析（编码检测 + 结构识别）
    ├── detector.py         # 地图类型自动检测
    ├── matcher.py          # 地区名模糊匹配引擎
    ├── mappings.py         # 多语言名称映射库（中→英 国家/省份）
    ├── themes.py           # 预设 + 自定义颜色主题
    └── generator.py        # pyecharts 地图生成器
```

## 🛠️ 技术栈

- [Streamlit](https://streamlit.io/) — Web UI 框架
- [pyecharts](https://pyecharts.org/) — ECharts Python 绑定
- [pandas](https://pandas.pydata.org/) — 数据处理
- [RapidFuzz](https://github.com/maxbachmann/RapidFuzz) — 模糊字符串匹配

## 📄 License

MIT
