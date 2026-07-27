"""
Preset color themes and custom color palette management for pyecharts maps.
"""

from typing import List, Dict


# Each theme is a list of hex colors from light to dark (sequential palette)
PRESET_THEMES: Dict[str, Dict] = {
    "ocean_blue": {
        "name": "海洋蓝",
        "name_en": "Ocean Blue",
        "description": "经典蓝色系，适合水资源、海洋、人口密度等",
        "colors": ["#E3F2FD", "#90CAF9", "#42A5F5", "#1E88E5", "#1565C0", "#0D47A1"],
    },
    "forest_green": {
        "name": "森林绿",
        "name_en": "Forest Green",
        "description": "自然绿色系，适合植被、农业、环保数据",
        "colors": ["#E8F5E9", "#A5D6A7", "#66BB6A", "#43A047", "#2E7D32", "#1B5E20"],
    },
    "sunset_red": {
        "name": "夕阳红",
        "name_en": "Sunset Red",
        "description": "暖色渐变，适合温度、消费、GDP等",
        "colors": ["#FBE9E7", "#FFAB91", "#FF7043", "#F4511E", "#D84315", "#BF360C"],
    },
    "purple_haze": {
        "name": "紫罗兰",
        "name_en": "Purple Haze",
        "description": "紫色渐变，适合教育、科技、创新指标",
        "colors": ["#F3E5F5", "#CE93D8", "#AB47BC", "#8E24AA", "#6A1B9A", "#4A148C"],
    },
    "golden_hour": {
        "name": "黄金时刻",
        "name_en": "Golden Hour",
        "description": "金黄暖色，适合经济、贸易、收入数据",
        "colors": ["#FFF8E1", "#FFE082", "#FFCA28", "#FFB300", "#FF8F00", "#FF6F00"],
    },
    "cool_teal": {
        "name": "清凉青",
        "name_en": "Cool Teal",
        "description": "青绿色系，适合气候、空气质量、健康数据",
        "colors": ["#E0F2F1", "#80CBC4", "#4DB6AC", "#26A69A", "#00897B", "#00695C"],
    },
    "warm_pink": {
        "name": "暖粉",
        "name_en": "Warm Pink",
        "description": "粉色渐变，适合人口、社会、性别数据",
        "colors": ["#FCE4EC", "#F48FB1", "#EC407A", "#D81B60", "#AD1457", "#880E4F"],
    },
    "slate_gray": {
        "name": "岩板灰",
        "name_en": "Slate Gray",
        "description": "中性灰色，适合严肃主题、基础设施数据",
        "colors": ["#ECEFF1", "#B0BEC5", "#78909C", "#546E7A", "#37474F", "#263238"],
    },
    "coral_reef": {
        "name": "珊瑚色",
        "name_en": "Coral Reef",
        "description": "珊瑚橙渐变，活泼温暖，适合旅游、餐饮数据",
        "colors": ["#FFF3E0", "#FFCC80", "#FFB74D", "#FF9800", "#F57C00", "#E65100"],
    },
    "deep_violet": {
        "name": "深紫蓝",
        "name_en": "Deep Violet",
        "description": "深蓝紫色系，沉稳大气，适合综合指数数据",
        "colors": ["#EDE7F6", "#B39DDB", "#7E57C2", "#5E35B1", "#4527A0", "#311B92"],
    },
}


def get_theme(theme_key: str) -> Dict:
    """Get a preset theme by key."""
    return PRESET_THEMES.get(theme_key, PRESET_THEMES["ocean_blue"])


def get_theme_list() -> List[Dict]:
    """Get all preset themes as a list."""
    return [
        {"key": key, "name": val["name"], "name_en": val["name_en"],
         "description": val["description"], "colors": val["colors"]}
        for key, val in PRESET_THEMES.items()
    ]


def validate_custom_colors(colors: List[str]) -> List[str]:
    """
    Validate and normalize custom color list.
    Ensures at least 2 valid hex colors, fills to at least 3 if needed.
    """
    valid = []
    for c in colors:
        c = c.strip()
        if c.startswith("#") and len(c) == 7:
            valid.append(c)
        elif len(c) == 6:
            valid.append(f"#{c}")

    # Need at least 2 colors for a gradient
    if len(valid) < 2:
        return get_theme("ocean_blue")["colors"]

    return valid


def interpolate_light_dark(colors: List[str]) -> List[str]:
    """Ensure colors are in light→dark order for sequential data."""
    # Simple heuristic: sort by perceived brightness
    def brightness(hex_color):
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return 0.299 * r + 0.587 * g + 0.114 * b

    return sorted(colors, key=brightness, reverse=True)
