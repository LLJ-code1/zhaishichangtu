# 债市周观察长图 — 工程规范 v1

> 本文件是整个 PSD 长图生成流水线的唯一规范。
> 所有脚本（Python / JSX）和 Codex 任务必须遵守本文件。
> 如果代码与本文件矛盾，以本文件为准。

> 2026-05-27 执行口径：当前生产主线是 `native_v3`。后续优化必须优先复用原 PSD 的标题条、白底板、浅黄滤镜、图标、阴影和水印；动态排版通过图层映射、文本测量、移动/拉伸原 PSD 组件完成，不回到整图覆盖或重画主体组件路线。

---

## 一、架构总览

```
Word (.docx)
    │
    ▼
[Step 1] Python 解析
    │  提取文字、表格、图表数据
    │  标注红色关键词
    ▼
content.json（中间格式）
    │
    ▼
[Step 2] Python 渲染资产
    │  表格 → table.png
    │  折线图 → chart_yield.png / chart_fund.png
    ▼
assets/ 目录（PNG 资产）
    │
    ▼
[Step 3] JSX PSD 组件替换引擎
    │  读取 content.json + assets/
    │  打开原始 PSD 模板
    │  按 schemas/psd_layer_map.json 定位原 PSD 图层
    │  隐藏旧文本/图片层
    │  创建 native_v3 可编辑文字层并替换图片
    │  后续自适应通过移动/拉伸原 PSD 组件实现
    ▼
输出 PSD + 导出 PNG
```

**关键原则：Python 负责数据、资产和文字排版计划；JSX 负责 Photoshop 图层定位、替换、分组和导出。** Python 不直接操作 PSD 图层，JSX 不直接理解 Word 段落。两者通过 `content.json` 和 `schemas/psd_layer_map.json` 解耦。

---

## 二、content.json 中间格式

### 顶层结构

```json
{
  "meta": {
    "date_range": "2026-05-15 至 2026-05-21",
    "display_date": "2026-5-21",
    "variant": "原版"
  },
  "sections": [
    { "type": "hero", ... },
    { "type": "market", ... },
    { "type": "analysis", ... },
    { "type": "outlook", ... },
    { "type": "strategy", ... },
    { "type": "disclaimer", ... }
  ],
  "assets": {
    "table": "assets/table.png",
    "chart_yield": "assets/chart_yield.png",
    "chart_fund": "assets/chart_fund.png",
    "chart_external_workbooks": [
      {
        "chart_xml": "word/charts/chart1.xml",
        "target": "file:///D:\\MyWorkSpace\\新Strats\\招行工作\\日常工作\\金葵花-数据底表.xlsx",
        "target_mode": "External"
      }
    ]
  }
}
```

### section 通用字段

每个 section 必须有：

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | string | section 类型标识 |
| `title` | string | section 标题文字（如"债市分析"） |
| `components` | array | 该 section 内部的组件列表 |

### 组件类型

| type | 用途 | 必填字段 |
|------|------|---------|
| `rich_text` | 正文段落（支持多色） | `segments: [{text, color}]` |
| `image` | 表格/图表图片 | `asset_key`, `width`, `aspect_ratio` |
| `subtitle` | 小标题（如"资金面"） | `text`, `icon`(可选) |
| `label` | 图表上方的说明行 | `segments: [{text, color}]` |

### segments 格式

```json
{
  "segments": [
    {"text": "展望后市，不改", "color": [24, 22, 20]},
    {"text": "资金面宽松的基本格局", "color": [232, 31, 31]},
    {"text": "。", "color": [24, 22, 20]}
  ]
}
```

**Python 生成 segments 时的规则：**

- 颜色只有两种：黑 `[24, 22, 20]` 和红 `[232, 31, 31]`。
- 相邻同色文字必须合并为一个 segment，不允许出现连续两个同色 segment。
- 标点符号跟随前面的文字颜色，不单独成 segment。
- 换行符 `\n` 写在 segment 的 text 内部，不拆成新 segment。

---

## 三、JSX 排版引擎设计

### 3.1 核心变量

```javascript
var CANVAS_WIDTH = 1125;          // 长图宽度（固定）
var CONTENT_LEFT = 88;            // 内容区左边距
var CONTENT_RIGHT = 1037;         // 内容区右边界
var CONTENT_WIDTH = 930;          // 内容区可用宽度（CONTENT_RIGHT - CONTENT_LEFT 取近似整数）

var current_y = 0;                // 全局排版指针，从头部底部开始
```

### 3.2 排版流程伪代码

```
current_y = 头部品牌区底部 y 坐标（从模板读取或硬编码，约 520px）

for each section in content.sections:
    current_y += SECTION_GAP                          // section 之间的间距
    current_y = draw_section_header(section.title, current_y)  // 画标题条
    current_y += HEADER_TO_CARD_GAP                   // 标题到卡片的间距
    card_start_y = current_y                          // 记录卡片起始位置

    for each component in section.components:
        current_y = draw_component(component, current_y)  // 画组件，返回底部 y
        current_y += COMPONENT_GAP                    // 组件间距

    card_end_y = current_y + CARD_PADDING_BOTTOM      // 卡片底部 padding
    draw_card_background(card_start_y, card_end_y)    // 回填卡片背景
    current_y = card_end_y

canvas 总高度 = current_y + FOOTER_MARGIN
```

**核心规则：所有 y 坐标由 `current_y` 累加产生，禁止在任何地方硬编码绝对 y 值。**

### 3.3 间距常量表

```javascript
// ===== 全局间距 =====
var SECTION_GAP           = 32;   // section 与 section 之间
var HEADER_TO_CARD_GAP    = 12;   // 标题条到内容卡片之间
var CARD_PADDING_TOP      = 45;   // 卡片内顶部 padding
var CARD_PADDING_BOTTOM   = 45;   // 卡片内底部 padding
var COMPONENT_GAP         = 24;   // 卡片内组件之间的垂直间距
var FOOTER_MARGIN         = 60;   // 最底部留白

// ===== 文字排版 =====
var BODY_FONT_SIZE        = 33;   // pt，正文字号
var BODY_LEADING          = 54;   // pt，正文行距（约 1.35 倍）
var SUBTITLE_FONT_SIZE    = 35;   // pt，小标题字号
var TITLE_FONT_SIZE       = 40;   // pt，section 标题字号
var LABEL_FONT_SIZE       = 31;   // pt，图表标注字号

// ===== 债市分析特殊布局 =====
var ICON_COLUMN_WIDTH     = 260;  // 左侧图标列宽度
var ICON_TEXT_GAP          = 30;   // 图标列到文字列的间距
var ANALYSIS_TEXT_LEFT     = CONTENT_LEFT + ICON_COLUMN_WIDTH + ICON_TEXT_GAP;
var ANALYSIS_TEXT_WIDTH    = CONTENT_RIGHT - ANALYSIS_TEXT_LEFT;
```

**间距调整规则：**
- 上面的数值是基准值，允许 ±5px 微调。
- 但调整必须改常量，不允许在某个 section 里直接写 magic number。
- 如果某处需要特殊间距，在常量表中新增带名字的常量。

### 3.3.1 native_v3 动态空隙规则

`native_v3` 不再用固定整图高度硬塞内容，也不从已经改过的 PSD 继续二次修改。每次生成都必须打开原始 PSD 模板，先完成文本、表格、图表替换，再根据替换后图层的真实 `bounds.bottom` 调整各 section 的留白和后续模块位置。

执行顺序：

1. 从原始 PSD 打开模板。
2. 隐藏旧文本/旧图片层，写入新的原生文字层和图表图片层。
3. 对每个 section 读取实际内容底部：正文组、表格、收益率图、资金利率图等都以 Photoshop 返回的真实 bounds 为准。
4. 白底板、内层卡片、浅色内容框只调整底部高度：`目标底部 = 内容底部 + 参考底部留白`。
5. 该 section 高度变化后，后续所有可见模块整体按同一个 delta 顺排上移或下移，保持模块之间约 17-20px 的原模板节奏。
6. 最终画布高度按风险提示文本底部加 footer 留白裁切。

参考底部留白来自原始 PSD 的人工排版效果，只作为当前审美基准，不代表每个 section 的固定高度：

| section | 内容锚点 | 内层底部留白 | 外层白底板底部留白 |
|---------|----------|--------------|--------------------|
| hero | 首屏正文 | - | 约 61px |
| market | 收益率曲线图 | 约 89px | 约 138px |
| analysis | 第二段风险偏好正文 | 约 143px | 约 184px |
| outlook | 后市展望正文 | 约 74px | 约 100px |
| strategy | 配置策略正文 | 约 79px | 约 101px |

关键注意：

- 这些空隙是“内容放完后的目标留白”，不是提前写死的 section 高度。
- 文本变长时，section 必须自动变高；文本变短时，section 可以自动收短，避免大段空白。
- Photoshop 原 PSD 中部分标题卡、标题文字、图标是 linked layers。顺排移动时必须把 linked layers 当成一组处理，并记录已处理图层，避免标题卡/标题文字被重复移动，导致标题耳朵压到上一模块。
- 动态空隙配置集中写在 `schemas/psd_layer_map.json` 的 `layout_adjustments.dynamic_gaps`，JSX 只读取配置执行，不在代码里散落 magic number。

### 3.4 组件渲染函数签名

每个 `draw_*` 函数必须遵守同一个契约：

```javascript
/**
 * @param {Object} component - content.json 中的组件对象
 * @param {Number} y_start - 该组件从哪个 y 开始画
 * @returns {Number} y_end - 该组件的底部 y（不含 gap，gap 由调用者加）
 */
function draw_rich_text(component, y_start) {
    // 1. 创建 PARAGRAPHTEXT 文本层（单层多色）
    // 2. 读取文本层实际边界高度
    // 3. return y_start + actual_height
}
```

**返回值是实际渲染高度，不是预估高度。** 这是动态排版的基础——上一个组件画完告诉下一个组件"我到哪了"。

### 3.5 高度测量方法

```javascript
function measureLayerHeight(layer) {
    var bounds = layer.bounds;
    return bounds[3].as("px") - bounds[1].as("px");
}

function measureLayerBottom(layer) {
    return layer.bounds[3].as("px");
}
```

创建文本层之后，**必须**用 `measureLayerHeight()` 获取实际高度，再推进 `current_y`。

不允许用「字数 × 行高 ÷ 每行字数」来预估高度，因为中英文混排、标点禁则、字体 metrics 都会导致预估不准。

### 3.6 卡片背景回填

卡片背景不能提前画（因为不知道高度），必须在所有内部组件画完后回填：

```javascript
function draw_card_background(y_top, y_bottom) {
    // 创建一个圆角矩形形状层
    // bounds: (CONTENT_LEFT - 10, y_top, CONTENT_RIGHT + 10, y_bottom)
    // 填充色: CREAM (255, 248, 235) 或 WHITE
    // 圆角: 12px
    // 将该层移到 section 组的最底部（视觉在最后面）
}
```

---

## 四、富文本规则（单层多色）

### 4.1 硬性规则

1. **一段正文 = 一个文本图层。** 绝对禁止为了改颜色拆层。
2. 段内多色使用 ActionDescriptor 的 `textStyleRange`。
3. 文本框使用段落模式（paragraph text），指定 box 宽度，让 PS 自动换行。
4. 不使用点文本（point text），因为点文本不会自动换行。

### 4.2 正式实现

正式 `native_v3` 生成流程已经使用单层富文本，不再使用 `native_text_runs` 多点文本层方案。

- Python 输出整段 `text` 和按字符区间记录的 `style_ranges`，保留每段文字、颜色、字号、行距、字体。
- JSX 在 `scripts/build_native_psd_v3.jsx` 中通过 `renderNativeTextBlock()` 创建一个 `PARAGRAPHTEXT` 文本框，一次性写入完整段落。
- JSX 通过 `styleTextLayerWithRanges()` 写入 ActionDescriptor 的 `textStyleRange`，给不同字符区间设置红黑样式。
- 动态排版读取该单层文本框的真实 `bounds.bottom`，继续按 `dynamic_gaps` 调整白底板和后续 section。

验证记录：

- 单独验证文件：`weeks/2026-05-25_2026-05-29/outputs/rich_text_test/首段单层富文本测试.psd`。
- 首屏验证结果：PSD 中只有 1 个新正文 `TEXT` 图层，文本长度 151，`textStyleRange` 数量 9，没有拆句式 `native_v3/top_intro` 图层。
- 正式流程验证结果：原版 `native_v3` 输出中 7 个红黑正文块均为 `native_v3_rich_text_*` 单层 `TEXT` 图层，旧拆句层数量为 0。
- 同步验证：单层富文本放入后，仍可按 `bounds.bottom` 执行动态空隙规则；首屏白底板从原始底部 1958 调整到 1683，下方模块整体上移 275px。

### 4.3 如果 ActionDescriptor 报错

1. 在 PS 中启用 ScriptListener 插件。
2. 手动创建一个文本框，输入一段话，选中部分文字改成红色。
3. 关闭 ScriptListener，在桌面找到 `ScriptingListenerJS.log`。
4. 把 log 中的 ActionDescriptor 代码提取出来，替换 `styleTextLayerWithRanges()` 内部实现。

这是最可靠的调试方法，因为 ScriptListener 录制的就是你 PS 版本的正确 API 调用。

---

## 五、section 具体规格

### 5.1 首屏（hero）

```
┌─────────────────────────────────┐
│  [品牌头部 - 保留原模板]           │  ← 不动，从原 PSD 保留
│  LOGO / 主标题 / 日期             │
├─────────────────────────────────┤
│  副标题: "国债收益率整体下行"       │  ← 50pt 黑体
│  [头图 - 保留原模板图片层]         │
│  摘要正文（红黑混排 segments）     │  ← rich_text 组件
│  └── 底部 padding 45px          │
└─────────────────────────────────┘
     ↕ SECTION_GAP 32px
```

**首屏卡片高度 = 副标题高度 + 头图高度 + 正文实际高度 + padding。** 不沿用旧模板的固定高度。

### 5.2 债市表现（market）

```
┌─ 标题条: "债市表现" ─────────────┐
│                                  │
│  一句话摘要（rich_text）          │
│  ↕ COMPONENT_GAP                 │
│  ┌── 表格区 ──────────────────┐  │
│  │ 小标题: 不同期限国债收益率   │  │
│  │ [table.png]                │  │
│  │ 小标题: 国债收益率曲线      │  │
│  │ [chart_yield.png]          │  │
│  └────────────────────────────┘  │
│  └── 底部 padding                │
└──────────────────────────────────┘
```

### 5.3 债市分析（analysis）

```
┌─ 标题条: "债市分析" ─────────────┐
│                                  │
│  ┌── 资金面 ─────────────────┐   │
│  │ [图标]  │  正文（rich_text）│   │  ← 左右分栏
│  │ 260px   │  剩余宽度        │   │
│  └─────────┴──────────────────┘   │
│  ↕ COMPONENT_GAP                  │
│  图表标注行（label）              │
│  [chart_fund.png]                 │
│  ↕ COMPONENT_GAP                  │
│  ┌── 市场风险偏好 ───────────┐   │
│  │ [图标]  │  正文（rich_text）│   │  ← 同样左右分栏
│  └─────────┴──────────────────┘   │
│  └── 底部 padding                 │
└───────────────────────────────────┘
```

**分栏规则：**
- 图标列宽度固定 `ICON_COLUMN_WIDTH = 260px`。
- 文字列从 `ANALYSIS_TEXT_LEFT` 开始。
- 文字列宽度 = `ANALYSIS_TEXT_WIDTH`。
- 图标和文字的 y 起点相同。
- 文字列高度算完后，取 max(图标高度, 文字高度) 作为该子区块的高度。
- 文字绝对不允许侵入图标列区域。

### 5.4 后市展望（outlook）

```
┌─ 标题条: "后市展望" ─────────────┐
│  正文（rich_text，红黑混排）      │
│  └── 底部 padding                │
└──────────────────────────────────┘
```

最简单的 section，一段正文。

### 5.5 配置策略（strategy）

结构同后市展望。

### 5.6 数据来源和风险提示（disclaimer）

```
┌──────────────────────────────────┐
│  数据来源：wind，截至2026年5月21日 │  ← 小字灰色
│  风险提示：xxxx                   │  ← 小字灰色
└──────────────────────────────────┘
```

---

## 六、图片资产规格

Python 生成的 PNG 资产需满足：

| 资产 | 宽度 | 背景 | 说明 |
|------|------|------|------|
| table.png | 900px | 透明或 #FFFBF3 | 国债收益率对比表格 |
| chart_yield.png | 860px | 透明 | 收益率曲线（近一年） |
| chart_fund.png | 770px | 透明 | DR001/DR007 资金利率图 |

- 所有图片 DPI 不低于 144（Retina 友好）。
- 图片放入 PSD 后的宽度按上表，高度由图片原始宽高比决定。
- 放入时居中于内容区（或居中于文字列，视 section 而定）。

---

## 七、PSD 图层结构

```
[原始模板图层 - 全部隐藏]
    ├── 旧 section 1 ...
    ├── 旧 section 2 ...
    └── ...

[品牌头部 - 保持可见]
    ├── 背景
    ├── LOGO
    ├── 主标题
    └── 日期 ← 更新文字

[v1_主体]  ← 新建的顶层组
    ├── 01_首屏
    │   ├── 首屏_卡片背景
    │   ├── 首屏_副标题
    │   └── 首屏_正文          ← 单层，含 textStyleRange 多色
    ├── 02_债市表现
    │   ├── 02_标题条
    │   ├── 02_卡片背景
    │   ├── 02_摘要
    │   ├── 02_表格标题
    │   ├── 02_table.png
    │   ├── 02_曲线标题
    │   └── 02_chart_yield.png
    ├── 03_债市分析
    │   ├── 03_标题条
    │   ├── 03_卡片背景
    │   ├── 03_资金面_图标
    │   ├── 03_资金面_正文     ← 单层多色
    │   ├── 03_资金面_图表标注
    │   ├── 03_chart_fund.png
    │   ├── 03_风险偏好_图标
    │   └── 03_风险偏好_正文   ← 单层多色
    ├── 04_后市展望
    │   ├── 04_标题条
    │   ├── 04_卡片背景
    │   └── 04_正文            ← 单层多色
    ├── 05_配置策略
    │   └── ...
    └── 06_风险提示
        └── 06_文字
```

命名规范：`{序号}_{描述}`，无空格，用下划线。

---

## 八、校验检查清单

PSD 生成完毕后，JSX 脚本自动执行以下检查并输出日志：

### 8.1 自动检查（JSX 内完成）

```javascript
var issues = [];

// 检查 1：相邻组件是否重叠
for (var i = 1; i < allLayers.length; i++) {
    var prevBottom = allLayers[i-1].bounds[3].as("px");
    var currTop = allLayers[i].bounds[1].as("px");
    if (currTop < prevBottom) {
        issues.push("OVERLAP: " + allLayers[i-1].name + " 和 " + allLayers[i].name);
    }
}

// 检查 2：任何两个组件之间的间距是否超过 80px（可能是不合理留白）
for (var i = 1; i < allLayers.length; i++) {
    var gap = allLayers[i].bounds[1].as("px") - allLayers[i-1].bounds[3].as("px");
    if (gap > 80) {
        issues.push("LARGE_GAP: " + gap + "px between " + allLayers[i-1].name + " / " + allLayers[i].name);
    }
}

// 检查 3：债市分析文字列是否侵入图标列
// （检查文字层 bounds[0] 是否 >= ANALYSIS_TEXT_LEFT）

// 检查 4：总高度是否合理（参考旧版约 7000px，允许 ±15%）
```

### 8.2 人工视觉检查（导出 PNG 后）

- [ ] 首屏无大面积空白
- [ ] 各 section 标题条视觉连续，间距均匀
- [ ] 债市分析图标和文字无叠加
- [ ] 表格和图表清晰、居中
- [ ] 日期、收益率数据与 Word 一致
- [ ] 底部风险提示完整
- [ ] 整体长图比例协调，无局部突然压缩或拉伸

---

## 九、每周更新流程

每周以 `native_v3` 为正式生产路线。核心原则是：Word 负责内容，原始 PSD 负责设计组件，Python 生成结构化内容和图表资产，Photoshop JSX 从原始 PSD 重新生成 PSD/PNG。

### 9.1 人工操作

1. 将新的三版 Word 放入 `weeks/<date-range>/inputs/word/variants/`。
2. 将本周原始 PSD 放入 `weeks/<date-range>/inputs/psd/`，正式生成必须从这个原始 PSD 打开。
3. 在 `scripts/project_paths.py` 更新 `CURRENT_WEEK` 和本周输入文件名。
4. 确认 `schemas/red_rules.json` 中的红字规则是否覆盖本周重点句。
5. 如果能拿到原始 Excel 底表，优先从 Excel/Office 导出图表；拿不到时才使用 DOCX chart XML + 脚本绘图近似。

### 9.2 自动化步骤

```bash
# Step 1: 解析三版 Word，并生成表格/图表资产与 native_v3 内容计划
/Users/a123/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  scripts/prepare_native_v3_content.py \
  --variant 原版 \
  --display-date 2026-5-27 \
  --source-date 2026年5月22日

# Step 2: 用 Photoshop 从原始 PSD 生成正式 PSD/PNG
osascript -e 'tell application "Adobe Photoshop 2025" to do javascript file "/Users/a123/Downloads/债市周观察/债市周观察/scripts/build_native_psd_v3.jsx"'

# Step 3: 回读 PSD 文本层，确认正文是单层富文本而不是拆句层
osascript -e 'tell application "Adobe Photoshop 2025" to do javascript file "/Users/a123/Downloads/债市周观察/债市周观察/scripts/inspect_native_v3_text_layers.jsx"'

# Step 4: 跑契约测试
/Users/a123/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  -m unittest \
  tests.test_engineering_contract \
  tests.test_native_v2_assets \
  tests.test_native_v3_editable_text \
  tests.test_native_v3_workflow_contract \
  -v
```

当前验收口径：

- 输出图宽度固定 `1125px`，高度由内容自适应裁切。
- 7 个红黑正文块均为 `native_v3_rich_text_*` 单层 `TEXT` 图层。
- 旧拆句式正文层数量应为 0。
- `work/native_v3/text_layers.tsv` 中每个富文本正文块应有 `style_ranges`。
- `psd_content/*.json` 应记录 `assets.chart_external_workbooks`；如果存在外部 Excel，优先提示走 Excel 导出图表路线。

### 9.3 渐进式验证

不要一次生成全部 6 个 section。按以下顺序逐步添加并检查：

```
Round 1: 只生成 hero + market        → 检查首屏空白、表格对齐
Round 2: 加入 analysis               → 检查分栏、图标文字不叠加
Round 3: 加入 outlook + strategy     → 检查正文排版、红色标注
Round 4: 加入 disclaimer             → 检查总高度、底部留白
```

每一轮导出 PNG 做视觉检查，确认无问题后再进入下一轮。

---

## 十、给 Codex 的系统提示

在让 Codex 编写或修改任何 Python / JSX 脚本时，在 prompt 开头加入：

```
你正在维护一个 Photoshop 长图自动生成项目。
请严格遵守 docs/engineering_spec.md 中的所有规范。
以下是必须遵守的核心规则：

1. 所有 y 坐标由 current_y 累加产生，禁止硬编码绝对 y 值。
2. 一段正文 = 一个文本层，多色用 textStyleRange，禁止拆层。
3. 文本层创建后必须用 layer.bounds 测量实际高度，用实际高度推进 current_y。
4. 间距只能用常量表中的命名常量，不允许在代码里写 magic number。
5. 卡片背景在内部组件全部画完后回填，不提前画。
6. 债市分析的图标列和文字列有固定边界，文字不得侵入图标区域。
7. 每个 draw_* 函数接收 y_start，返回 y_end。
8. Python 只负责数据和图片资产，JSX 只负责排版，两者通过 content.json 解耦。

如果你不确定某个参数或做法，先问我，不要猜测后自行实现。
```

---

## 十一、文件清单

完成本规范后，项目应包含以下新文件：

```
scripts/
├── extract_word_psd_content.py  ← Python: 三版 Word → psd_content/*.json
├── prepare_basic_v0_assets.py   ← Python: 表格/图表 PNG 资产
├── prepare_native_v3_content.py ← Python: native_v3 内容计划和单层富文本 style_ranges
├── build_native_psd_v3.jsx      ← JSX: renderNativeTextBlock() + styleTextLayerWithRanges()
├── inspect_native_v3_text_layers.jsx ← JSX: 回读 PSD 文本层校验
└── layout_constants.jsx         ← JSX: 所有间距/字号/颜色常量

docs/
├── engineering_spec.md     ← 本文件
└── ...

schemas/psd_layer_map.json  ← PSD 语义图层映射和动态空隙配置
weeks/<date-range>/work/psd_content/*.json
weeks/<date-range>/work/native_v3/content.json
weeks/<date-range>/work/basic_v0/assets/
```
