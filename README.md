# 债市周观察长图项目

## 项目目标

把“金葵花债市周度复盘”Word 素材，转成招商银行金葵花风格的债市周观察长图，并沉淀成可复用的长图生产项目。

当前素材周期：2026-05-15 至 2026-05-21。

当前制作周目录：`weeks/2026-05-25_2026-05-29/`。

## 当前状态

当前推荐方向已经调整为“PSD 原生文本 v3”：

- 不再把整张新版 PNG 贴到 PSD 顶层。
- 不再用脚本重画卡片、标题条和阴影。
- 保留原 PSD 内的标题卡、白底板、浅黄滤镜、圆角阴影、图标和品牌水印。
- 红黑正文生成 Photoshop 单层段落 `TEXT` 图层，通过 `textStyleRange` 做局部标红，最终 PSD 可编辑。
- 每次生成都从原始 PSD 打开，不从已经改过的 PSD 二次修改。
- 内容放入后按 Photoshop 返回的真实 `bounds.bottom` 调整白底板和后续模块空隙。
- 表格和图表仍作为图片层替换到原 PSD 占位层。

这一方向已通过 `原生文本v3` 验证：原版输出中 7 个红黑正文块均为 `native_v3_rich_text_*` 单层 Photoshop 文字层，旧拆句式正文层数量为 0；字体为 `SourceHanSansCN-Medium`，红黑强调和 `1.`、`2.`、`固收+`、`5月LPR`、`DR007` 等符号均已保留。动态空隙已经接入正式流程，原版输出高度为 `1125 × 6486`。

当前仍需继续打磨的是图表和表格。现有图表/表格仍是脚本近似绘制，不应假装已经完全等同手工版。最接近原版的修法是拿到 Word 图表外部引用的 Excel：`D:\MyWorkSpace\新Strats\招行工作\日常工作\金葵花-数据底表.xlsx`，由 Excel/Office 直接导出图表再放回 PSD；拿不到 Excel 时，继续解析 DOCX 的 `chart*.xml`、`style*.xml`、`colors*.xml` 并用脚本尽量复刻。

详细问题见 [docs/待解决.md](docs/待解决.md) 和 [docs/问题记录.md](docs/问题记录.md)。

基础长图 v0 方案见 [docs/superpowers/specs/2026-05-25-photoshop-basic-long-image-design.md](docs/superpowers/specs/2026-05-25-photoshop-basic-long-image-design.md)，已证明“重画主体”会丢失模板质感。后续实现应以 `native_v3` 为主，不再走“重新绘制 PSD 主体”的路线。

## 目录说明

```text
.
├── README.md
├── docs/
│   ├── 待解决.md
│   ├── 问题记录.md
│   ├── 制作日志.md
│   ├── engineering_spec.md
│   └── 内容拆解与PSD输入规则.md
├── schemas/
│   ├── psd_layer_map.json
│   ├── psd_content_schema.json
│   └── red_rules.json
├── scripts/
│   ├── project_paths.py
│   ├── layout_constants.jsx
│   ├── build_long_images.py
│   ├── extract_word_psd_content.py
│   ├── prepare_basic_v0_assets.py
│   ├── prepare_native_v1_content.py
│   ├── prepare_native_v2_content.py
│   ├── prepare_native_v3_content.py
│   ├── build_native_psd_v1.jsx
│   ├── build_native_psd_v2.jsx
│   ├── build_native_psd_v3.jsx
│   ├── inspect_native_v3_text_layers.jsx
│   ├── list_psd_layers.jsx
│   ├── make_original_psd_overlay.jsx
│   └── export_psd_right_preview.jsx
├── weeks/
│   └── 2026-05-25_2026-05-29/
│       ├── inputs/
│       ├── work/
│       └── outputs/
└── 债市周观察/
    └── 周报模板/
```

## 素材口径

- `weeks/2026-05-25_2026-05-29/inputs/word/raw/`：原始 Word，用于理解结构和对比。
- `weeks/2026-05-25_2026-05-29/inputs/word/edited/`：修改版 Word，本轮主要内容来源。
- `weeks/2026-05-25_2026-05-29/inputs/word/variants/`：用户整理的三版 Word，作为 PSD 输入的内容母版。
- `weeks/2026-05-25_2026-05-29/inputs/psd/`：原始 Photoshop 模板。
- `weeks/2026-05-25_2026-05-29/inputs/reference_long_images/`：旧版参考长图。
- `weeks/2026-05-25_2026-05-29/outputs/20260521新版/`：第一轮 PNG/overlay PSD 草稿，已不作为推荐方向。
- `weeks/2026-05-25_2026-05-29/outputs/native_v1/`：PSD 原生组件替换实验版，证明保留模板组件是正确方向。
- `weeks/2026-05-25_2026-05-29/outputs/native_v2/`：透明图表和富文本图片修正版，视觉接近但正文不可编辑。
- `weeks/2026-05-25_2026-05-29/outputs/native_v3/`：当前主线，红黑正文为可编辑 Photoshop `TEXT` 图层。

## 当前生成结果

```text
weeks/2026-05-25_2026-05-29/outputs/20260521新版/
├── 金葵花债市周观察20260521_原版.png
├── 金葵花债市周观察20260521_固收+.png
├── 金葵花债市周观察20260521_债.png
└── 金葵花债市周观察20260521_原版.psd

weeks/2026-05-25_2026-05-29/outputs/native_v1/
├── 金葵花债市周观察20260521_原生组件v1.png
└── 金葵花债市周观察20260521_原生组件v1.psd

weeks/2026-05-25_2026-05-29/outputs/native_v2/
├── 金葵花债市周观察20260521_原生组件v2.png
└── 金葵花债市周观察20260521_原生组件v2.psd

weeks/2026-05-25_2026-05-29/outputs/native_v3/
├── 金葵花债市周观察20260521_原生文本v3.png
├── 金葵花债市周观察20260521_原生文本v3.psd
├── 金葵花债市周观察20260521_原版_原生文本v3.png
└── 金葵花债市周观察20260521_原版_原生文本v3.psd
```

三版 PNG 的差异主要在首屏开头文案；下方主体结构基本一致。策略部分按本轮要求沿用原策略，没有做实质改写。当前应优先打磨 `原生文本v3`，再扩展到固收+和债市两个首屏版本。

## 现有脚本

- `scripts/build_long_images.py`：从 Word 提取文本、表格和图表数据，并基于旧长图底图生成三版 PNG。
- `scripts/extract_word_psd_content.py`：读取用户整理的三版 Word，生成 PSD 可消费的结构化 JSON，套用固定策略、标红规则和债市版口径修正，并记录 Word 图表外部 Excel/OLE 来源。
- `scripts/prepare_basic_v0_assets.py`：解析修改版 Word，生成表格/图表等中间资产；供后续 PSD 替换脚本复用。当前图表为脚本近似绘制，Excel 底表导出是高保真路线。
- `scripts/prepare_native_v1_content.py`：生成原生组件替换版所需的结构化内容，目前已接入三版 Word 解析后的 `weeks/2026-05-25_2026-05-29/work/psd_content/原版.json`。
- `scripts/prepare_native_v2_content.py`：生成透明图表和富文本图片资产，用于验证红字和裁切问题。
- `scripts/prepare_native_v3_content.py`：生成可编辑原生文字层计划，输出整段 `text` 和 `style_ranges`，供 Photoshop 创建单层段落富文本。
- `scripts/project_paths.py`：集中定义当前制作周目录，后续换周优先改这里。
- `scripts/build_native_psd_v1.jsx`：打开原 PSD，保留原组件，只替换文字、表格和图表并导出 PNG/PSD。
- `scripts/build_native_psd_v2.jsx`：使用透明富文本 PNG 替换正文，解决视觉问题但正文不可编辑。
- `scripts/build_native_psd_v3.jsx`：使用 Photoshop `PARAGRAPHTEXT + textStyleRange` 生成红黑正文，并按真实图层边界执行动态空隙调整，是当前推荐 PSD 路线。
- `scripts/inspect_native_v3_text_layers.jsx`：回读 v3 PSD，检查正文图层类型、字体、颜色和 `textStyleRange` 数量。
- `scripts/list_psd_layers.jsx`：在 Photoshop 中导出 PSD 图层位置，用于理解模板结构。
- `scripts/make_original_psd_overlay.jsx`：在原 PSD 中贴入新版原版 PNG，另存为新版 PSD。
- `scripts/export_psd_right_preview.jsx`：用 Photoshop 从新版 PSD 导出右侧长图预览，用于校验 PSD 合成效果。

## 建议的下一阶段方向

下一阶段不要回到“整图覆盖”或“重画卡片”路线。建议在 `native_v3` 上继续：

1. 建立 PSD 图层映射表：日期、首屏标题、首屏正文、债市表现一句话、表格、图表、债市分析、后市展望、风险提示。
2. 优化可编辑正文图层：当前红黑段落已是单层段落富文本，下一步精调字号、行距、字重和文本框边界。
3. 解决图表风格：优先找到外部 Excel 底表并直接导出图表；拿不到底表时，再解析 Office 图表样式 XML 或建立脚本视觉参数。
4. 在保留原生组件质感的前提下，继续微调动态空隙和卡片底部留白。
5. 确认一版原版 PSD 稳定后，再扩展固收+和债市两个首屏版本。
