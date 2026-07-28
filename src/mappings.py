"""
Multi-language name mapping library.
Maps various name formats → pyecharts standard names.

CRITICAL: pyecharts CDN china.js uses FULL names WITH administrative suffixes
(e.g. "北京市" not "北京", "河北省" not "河北").
All mappings MUST target these exact names.
"""

# ============================================================
# China province standard names — MUST EXACTLY MATCH china.js
# These are the 34 region names from pyecharts CDN china.js (v6)
# ============================================================

CHINA_STANDARD_NAMES = [
    # Municipalities
    "北京市", "天津市", "上海市", "重庆市",
    # Provinces
    "河北省", "山西省", "辽宁省", "吉林省",
    "黑龙江省", "江苏省", "浙江省", "安徽省",
    "福建省", "江西省", "山东省", "河南省",
    "湖北省", "湖南省", "广东省", "海南省",
    "四川省", "贵州省", "云南省", "陕西省",
    "甘肃省", "青海省", "台湾省",
    # Autonomous Regions
    "内蒙古自治区", "广西壮族自治区", "西藏自治区",
    "宁夏回族自治区", "新疆维吾尔自治区",
    # SARs
    "香港特别行政区", "澳门特别行政区",
]

# Quick set for "is this already a valid name?" checks
_CHINA_STANDARD_SET = set(CHINA_STANDARD_NAMES)


# ============================================================
# CN_PROVINCE_MAP: Every possible variant → EXACT china.js name
# Covers: full names with suffix, bare names, English, pinyin, old names
# ============================================================

CN_PROVINCE_MAP = {
    # ═══ Municipalities ═══
    # 北京
    "北京市": "北京市", "北京": "北京市",
    "Beijing": "北京市", "Peking": "北京市",
    "beijing": "北京市",

    # 天津
    "天津市": "天津市", "天津": "天津市",
    "Tianjin": "天津市", "Tientsin": "天津市",
    "tianjin": "天津市",

    # 上海
    "上海市": "上海市", "上海": "上海市",
    "Shanghai": "上海市",
    "shanghai": "上海市",

    # 重庆
    "重庆市": "重庆市", "重庆": "重庆市",
    "Chongqing": "重庆市", "Chungking": "重庆市",
    "chongqing": "重庆市",

    # ═══ Provinces ═══
    # 河北
    "河北省": "河北省", "河北": "河北省",
    "Hebei": "河北省", "Hopeh": "河北省",
    "hebei": "河北省",

    # 山西
    "山西省": "山西省", "山西": "山西省",
    "Shanxi": "山西省", "Shansi": "山西省",
    "shanxi": "山西省",

    # 辽宁
    "辽宁省": "辽宁省", "辽宁": "辽宁省",
    "Liaoning": "辽宁省",
    "liaoning": "辽宁省",

    # 吉林
    "吉林省": "吉林省", "吉林": "吉林省",
    "Jilin": "吉林省", "Kirin": "吉林省",
    "jilin": "吉林省",

    # 黑龙江
    "黑龙江省": "黑龙江省", "黑龙江": "黑龙江省",
    "Heilongjiang": "黑龙江省",
    "heilongjiang": "黑龙江省",

    # 江苏
    "江苏省": "江苏省", "江苏": "江苏省",
    "Jiangsu": "江苏省", "Kiangsu": "江苏省",
    "jiangsu": "江苏省",

    # 浙江
    "浙江省": "浙江省", "浙江": "浙江省",
    "Zhejiang": "浙江省", "Chekiang": "浙江省",
    "zhejiang": "浙江省",

    # 安徽
    "安徽省": "安徽省", "安徽": "安徽省",
    "Anhui": "安徽省", "Anhwei": "安徽省",
    "anhui": "安徽省",

    # 福建
    "福建省": "福建省", "福建": "福建省",
    "Fujian": "福建省", "Fukien": "福建省",
    "fujian": "福建省",

    # 江西
    "江西省": "江西省", "江西": "江西省",
    "Jiangxi": "江西省", "Kiangsi": "江西省",
    "jiangxi": "江西省",

    # 山东
    "山东省": "山东省", "山东": "山东省",
    "Shandong": "山东省", "Shantung": "山东省",
    "shandong": "山东省",

    # 河南
    "河南省": "河南省", "河南": "河南省",
    "Henan": "河南省", "Honan": "河南省",
    "henan": "河南省",

    # 湖北
    "湖北省": "湖北省", "湖北": "湖北省",
    "Hubei": "湖北省", "Hupeh": "湖北省",
    "hubei": "湖北省",

    # 湖南
    "湖南省": "湖南省", "湖南": "湖南省",
    "Hunan": "湖南省",
    "hunan": "湖南省",

    # 广东
    "广东省": "广东省", "广东": "广东省",
    "Guangdong": "广东省", "Kwangtung": "广东省",
    "guangdong": "广东省",

    # 海南
    "海南省": "海南省", "海南": "海南省",
    "Hainan": "海南省",
    "hainan": "海南省",

    # 四川
    "四川省": "四川省", "四川": "四川省",
    "Sichuan": "四川省", "Szechuan": "四川省", "Szechwan": "四川省",
    "sichuan": "四川省",

    # 贵州
    "贵州省": "贵州省", "贵州": "贵州省",
    "Guizhou": "贵州省", "Kweichow": "贵州省",
    "guizhou": "贵州省",

    # 云南
    "云南省": "云南省", "云南": "云南省",
    "Yunnan": "云南省",
    "yunnan": "云南省",

    # 陕西
    "陕西省": "陕西省", "陕西": "陕西省",
    "Shaanxi": "陕西省", "Shensi": "陕西省",
    "shaanxi": "陕西省",

    # 甘肃
    "甘肃省": "甘肃省", "甘肃": "甘肃省",
    "Gansu": "甘肃省", "Kansu": "甘肃省",
    "gansu": "甘肃省",

    # 青海
    "青海省": "青海省", "青海": "青海省",
    "Qinghai": "青海省", "Tsinghai": "青海省",
    "qinghai": "青海省",

    # 台湾
    "台湾省": "台湾省", "台湾": "台湾省",
    "Taiwan": "台湾省", "taiwan": "台湾省",

    # ═══ Autonomous Regions ═══
    # 内蒙古
    "内蒙古自治区": "内蒙古自治区", "内蒙古": "内蒙古自治区",
    "Inner Mongolia": "内蒙古自治区", "Nei Mongol": "内蒙古自治区",
    "inner mongolia": "内蒙古自治区",

    # 广西
    "广西壮族自治区": "广西壮族自治区", "广西": "广西壮族自治区",
    "Guangxi": "广西壮族自治区", "Kwangsi": "广西壮族自治区",
    "guangxi": "广西壮族自治区",

    # 西藏
    "西藏自治区": "西藏自治区", "西藏": "西藏自治区",
    "Tibet": "西藏自治区", "Xizang": "西藏自治区",
    "tibet": "西藏自治区", "xizang": "西藏自治区",

    # 宁夏
    "宁夏回族自治区": "宁夏回族自治区", "宁夏": "宁夏回族自治区",
    "Ningxia": "宁夏回族自治区", "Ningsia": "宁夏回族自治区",
    "ningxia": "宁夏回族自治区",

    # 新疆
    "新疆维吾尔自治区": "新疆维吾尔自治区", "新疆": "新疆维吾尔自治区",
    "Xinjiang": "新疆维吾尔自治区", "Sinkiang": "新疆维吾尔自治区",
    "xinjiang": "新疆维吾尔自治区",

    # ═══ Special Administrative Regions ═══
    # 香港
    "香港特别行政区": "香港特别行政区", "香港": "香港特别行政区",
    "Hong Kong": "香港特别行政区", "HongKong": "香港特别行政区",
    "hong kong": "香港特别行政区", "hongkong": "香港特别行政区",

    # 澳门
    "澳门特别行政区": "澳门特别行政区", "澳门": "澳门特别行政区",
    "Macau": "澳门特别行政区", "Macao": "澳门特别行政区",
    "macau": "澳门特别行政区", "macao": "澳门特别行政区",

    # ═══ Additional fuzzy: bare names → full (for short variants that might appear) ═══
    # Complete coverage: all bare names map to their full form
    "内蒙": "内蒙古自治区",
    "广西省": "广西壮族自治区",  # common mistake
    "新疆省": "新疆维吾尔自治区",  # common mistake
    "西藏省": "西藏自治区",  # common mistake
    "宁夏省": "宁夏回族自治区",  # common mistake
}


# ============================================================
# Chinese → English country names (for pyecharts world map)
# pyecharts world map uses STANDARD ENGLISH country names
# ============================================================

CN_TO_EN_COUNTRY = {
    # ── Asia ──
    "中国": "China", "中华人民共和国": "China",
    "日本": "Japan", "日本国": "Japan",
    "韩国": "South Korea", "大韩民国": "South Korea", "南朝鲜": "South Korea",
    "朝鲜": "North Korea", "朝鲜民主主义人民共和国": "North Korea", "北朝鲜": "North Korea",
    "蒙古": "Mongolia", "蒙古国": "Mongolia",
    "印度": "India", "印度共和国": "India",
    "越南": "Vietnam", "越南社会主义共和国": "Vietnam",
    "老挝": "Laos", "老挝人民民主共和国": "Laos",
    "柬埔寨": "Cambodia", "柬埔寨王国": "Cambodia",
    "泰国": "Thailand", "泰王国": "Thailand",
    "缅甸": "Myanmar", "缅甸联邦共和国": "Myanmar", "Burma": "Myanmar",
    "马来西亚": "Malaysia",
    "新加坡": "Singapore",
    "印度尼西亚": "Indonesia",
    "菲律宾": "Philippines",
    "文莱": "Brunei", "文莱达鲁萨兰国": "Brunei",
    "东帝汶": "East Timor",
    "巴基斯坦": "Pakistan",
    "孟加拉国": "Bangladesh", "孟加拉": "Bangladesh",
    "尼泊尔": "Nepal",
    "不丹": "Bhutan",
    "斯里兰卡": "Sri Lanka",
    "马尔代夫": "Maldives",
    "哈萨克斯坦": "Kazakhstan",
    "乌兹别克斯坦": "Uzbekistan",
    "土库曼斯坦": "Turkmenistan",
    "吉尔吉斯斯坦": "Kyrgyzstan",
    "塔吉克斯坦": "Tajikistan",
    "阿富汗": "Afghanistan",
    "伊朗": "Iran", "伊朗伊斯兰共和国": "Iran",
    "伊拉克": "Iraq",
    "沙特阿拉伯": "Saudi Arabia", "沙特": "Saudi Arabia",
    "也门": "Yemen",
    "阿曼": "Oman",
    "阿拉伯联合酋长国": "United Arab Emirates", "阿联酋": "United Arab Emirates",
    "卡塔尔": "Qatar",
    "巴林": "Bahrain",
    "科威特": "Kuwait",
    "约旦": "Jordan",
    "黎巴嫩": "Lebanon",
    "叙利亚": "Syria",
    "以色列": "Israel",
    "巴勒斯坦": "Palestine",
    "土耳其": "Turkey", "土耳其共和国": "Turkey",
    "塞浦路斯": "Cyprus",
    "格鲁吉亚": "Georgia",
    "亚美尼亚": "Armenia",
    "阿塞拜疆": "Azerbaijan",

    # ── Europe ──
    "俄罗斯": "Russia", "俄罗斯联邦": "Russia",
    "英国": "United Kingdom", "大不列颠及北爱尔兰联合王国": "United Kingdom",
    "法国": "France", "法兰西共和国": "France",
    "德国": "Germany", "德意志联邦共和国": "Germany",
    "意大利": "Italy", "意大利共和国": "Italy",
    "西班牙": "Spain", "西班牙王国": "Spain",
    "葡萄牙": "Portugal",
    "荷兰": "Netherlands",
    "比利时": "Belgium",
    "卢森堡": "Luxembourg",
    "瑞士": "Switzerland",
    "奥地利": "Austria",
    "瑞典": "Sweden",
    "挪威": "Norway",
    "丹麦": "Denmark",
    "芬兰": "Finland",
    "冰岛": "Iceland",
    "爱尔兰": "Ireland",
    "波兰": "Poland",
    "捷克": "Czech Republic", "捷克共和国": "Czech Republic",
    "斯洛伐克": "Slovakia",
    "匈牙利": "Hungary",
    "罗马尼亚": "Romania",
    "保加利亚": "Bulgaria",
    "塞尔维亚": "Serbia",
    "克罗地亚": "Croatia",
    "斯洛文尼亚": "Slovenia",
    "波黑": "Bosnia and Herzegovina", "波斯尼亚和黑塞哥维那": "Bosnia and Herzegovina",
    "黑山": "Montenegro",
    "北马其顿": "North Macedonia", "马其顿": "North Macedonia",
    "阿尔巴尼亚": "Albania",
    "希腊": "Greece",
    "乌克兰": "Ukraine",
    "白俄罗斯": "Belarus",
    "摩尔多瓦": "Moldova",
    "立陶宛": "Lithuania",
    "拉脱维亚": "Latvia",
    "爱沙尼亚": "Estonia",
    "安道尔": "Andorra",
    "摩纳哥": "Monaco",
    "列支敦士登": "Liechtenstein",
    "马耳他": "Malta",
    "圣马力诺": "San Marino",
    "梵蒂冈": "Vatican",

    # ── Africa ──
    "埃及": "Egypt",
    "利比亚": "Libya",
    "突尼斯": "Tunisia",
    "阿尔及利亚": "Algeria",
    "摩洛哥": "Morocco",
    "苏丹": "Sudan",
    "南苏丹": "South Sudan",
    "埃塞俄比亚": "Ethiopia",
    "厄立特里亚": "Eritrea",
    "吉布提": "Djibouti",
    "索马里": "Somalia",
    "肯尼亚": "Kenya",
    "坦桑尼亚": "Tanzania",
    "乌干达": "Uganda",
    "卢旺达": "Rwanda",
    "布隆迪": "Burundi",
    "刚果民主共和国": "Democratic Republic of the Congo",
    "刚果（金）": "Democratic Republic of the Congo",
    "刚果(金)": "Democratic Republic of the Congo",
    "刚果共和国": "Congo", "刚果（布）": "Congo", "刚果(布)": "Congo", "刚果": "Congo",
    "加蓬": "Gabon",
    "赤道几内亚": "Equatorial Guinea",
    "喀麦隆": "Cameroon",
    "中非": "Central African Republic", "中非共和国": "Central African Republic",
    "乍得": "Chad",
    "尼日尔": "Niger",
    "尼日利亚": "Nigeria",
    "加纳": "Ghana",
    "科特迪瓦": "Cote d'Ivoire",
    "利比里亚": "Liberia",
    "塞拉利昂": "Sierra Leone",
    "几内亚": "Guinea",
    "几内亚比绍": "Guinea-Bissau",
    "塞内加尔": "Senegal",
    "冈比亚": "Gambia",
    "马里": "Mali",
    "布基纳法索": "Burkina Faso",
    "贝宁": "Benin",
    "多哥": "Togo",
    "毛里塔尼亚": "Mauritania",
    "安哥拉": "Angola",
    "赞比亚": "Zambia",
    "津巴布韦": "Zimbabwe",
    "马拉维": "Malawi",
    "莫桑比克": "Mozambique",
    "博茨瓦纳": "Botswana",
    "纳米比亚": "Namibia",
    "南非": "South Africa",
    "莱索托": "Lesotho",
    "斯威士兰": "Eswatini",
    "马达加斯加": "Madagascar",
    "毛里求斯": "Mauritius",
    "塞舌尔": "Seychelles",
    "科摩罗": "Comoros",

    # ── North America ──
    "美国": "United States", "美利坚合众国": "United States", "美囯": "United States",
    "加拿大": "Canada",
    "墨西哥": "Mexico",
    "危地马拉": "Guatemala",
    "伯利兹": "Belize",
    "萨尔瓦多": "El Salvador",
    "洪都拉斯": "Honduras",
    "尼加拉瓜": "Nicaragua",
    "哥斯达黎加": "Costa Rica",
    "巴拿马": "Panama",
    "古巴": "Cuba",
    "牙买加": "Jamaica",
    "海地": "Haiti",
    "多米尼加": "Dominican Republic", "多米尼加共和国": "Dominican Republic",
    "巴哈马": "Bahamas",
    "特立尼达和多巴哥": "Trinidad and Tobago",

    # ── South America ──
    "巴西": "Brazil",
    "阿根廷": "Argentina",
    "智利": "Chile",
    "秘鲁": "Peru",
    "哥伦比亚": "Colombia",
    "委内瑞拉": "Venezuela",
    "厄瓜多尔": "Ecuador",
    "玻利维亚": "Bolivia",
    "巴拉圭": "Paraguay",
    "乌拉圭": "Uruguay",
    "圭亚那": "Guyana",
    "苏里南": "Suriname",

    # ── Oceania ──
    "澳大利亚": "Australia", "澳洲": "Australia",
    "新西兰": "New Zealand",
    "巴布亚新几内亚": "Papua New Guinea",
    "斐济": "Fiji",
    "所罗门群岛": "Solomon Islands",
    "瓦努阿图": "Vanuatu",
    "萨摩亚": "Samoa",
    "汤加": "Tonga",
    "密克罗尼西亚": "Micronesia",
    "帕劳": "Palau",
    "马绍尔群岛": "Marshall Islands",
    "基里巴斯": "Kiribati",
    "瑙鲁": "Nauru",
    "图瓦卢": "Tuvalu",

    # ── Others ──
    "格陵兰": "Greenland",
    "南极洲": "Antarctica",
}


# ============================================================
# Non-standard English names → pyecharts world map standard
# ============================================================

EN_COUNTRY_STANDARD = {
    # Common abbreviations / variations
    "USA": "United States", "U.S.A.": "United States", "U.S.": "United States",
    "US": "United States", "America": "United States",
    "UK": "United Kingdom", "U.K.": "United Kingdom",
    "UAE": "United Arab Emirates",
    "Korea, South": "South Korea", "Republic of Korea": "South Korea",
    "Korea, North": "North Korea", "DPRK": "North Korea",
    "DR Congo": "Democratic Republic of the Congo",
    "Congo, DRC": "Democratic Republic of the Congo",
    "Congo, Republic of": "Congo",
    "Ivory Coast": "Cote d'Ivoire",
    "Czechia": "Czech Republic",
    "Slovak Republic": "Slovakia",
    "Bosnia": "Bosnia and Herzegovina",
    "Vatican City": "Vatican",
    "East Timor": "East Timor", "Timor-Leste": "East Timor",
    "Russia Federation": "Russia", "Russian Federation": "Russia",
    "Iran, Islamic Republic of": "Iran",
    "Syrian Arab Republic": "Syria",
    "Lao PDR": "Laos", "Lao People's Democratic Republic": "Laos",
    "Brunei Darussalam": "Brunei",
    "Macao": "Macau",
    "Taiwan, Province of China": "Taiwan",
    "Hong Kong SAR": "Hong Kong",
    "Macao SAR": "Macau",
    "Korea, Republic of": "South Korea",
    "Korea, Democratic People's Republic of": "North Korea",
    "Viet Nam": "Vietnam",
    "Russian": "Russia",
    "Türkiye": "Turkey", "Turkiye": "Turkey",
    "Myanmar (Burma)": "Myanmar",
    "Eswatini (Swaziland)": "Eswatini", "Swaziland": "Eswatini",
}


# ============================================================
# Map type names → pyecharts maptype parameter
# ============================================================

MAPTYPE_NAMES = {
    "china": "china",
    "world": "world",
    "united states": "United States", "usa": "United States",
    "japan": "Japan",
    "france": "France",
    "germany": "Germany",
    "united kingdom": "United Kingdom", "uk": "United Kingdom",
    "canada": "Canada",
    "australia": "Australia",
    "brazil": "Brazil",
    "russia": "Russia",
    "india": "India",
    "italy": "Italy",
    "spain": "Spain",
    "south korea": "South Korea",
    "mexico": "Mexico",
    "indonesia": "Indonesia",
    "turkey": "Turkey",
    "netherlands": "Netherlands",
    "switzerland": "Switzerland",
    "sweden": "Sweden",
    "poland": "Poland",
    "belgium": "Belgium",
    "austria": "Austria",
    "norway": "Norway",
    "denmark": "Denmark",
    "finland": "Finland",
    "portugal": "Portugal",
    "greece": "Greece",
    "argentina": "Argentina",
    "chile": "Chile",
    "colombia": "Colombia",
    "south africa": "South Africa",
    "egypt": "Egypt",
    "saudi arabia": "Saudi Arabia",
    "thailand": "Thailand",
    "vietnam": "Vietnam",
    "malaysia": "Malaysia",
    "philippines": "Philippines",
    "new zealand": "New Zealand",
}
