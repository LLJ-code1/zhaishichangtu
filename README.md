# 债市周观察长图项目

## 项目目标

把“金葵花债市周度复盘”Word 素材，转成招商银行金葵花风格的债市周观察长图，并沉淀成可复用的自动化生产流程。

当前素材周期：`2026-05-22 至 2026-05-28`  
当前制作周目录：`weeks/2026-06-01_2026-06-05/`

## 当前状态

当前主线是 `native_v3`：保留原 PSD 的标题卡、白底板、浅黄滤镜、圆角阴影、图标和品牌水印，只替换正文、表格和图表内容。

- 正文采用 Photoshop 单层段落 `TEXT` 图层，并通过 `textStyleRange` 实现局部标红。
- 三版内容已按本周 Word 生成：`原版`、`固收+`、`债市`。
- 本周输出为三版 PSD 和 PNG；因 PSD/PNG 文件体积较大，GitHub 当前分支只保存生产流程、输入说明和小体积素材，不保存最终大文件。
- 最终大文件保留在本地：`weeks/2026-06-01_2026-06-05/outputs/native_v3/`。

## 目录说明

```text
.
├── README.md
├── docs/                         # 工程规范、制作记录和历史问题记录
├── schemas/                      # PSD 图层映射、内容 schema、标红规则
├── scripts/                      # Word 解析、图表生成、PSD 生成和检查脚本
├── tests/                        # 生产流程契约测试
└── weeks/
    ├── 2026-05-25_2026-05-29/    # 上一周生产包
    └── 2026-06-01_2026-06-05/    # 当前生产包
```

每个 `weeks/<date_range>/` 目录按以下结构组织：

```text
inputs/    # 本周 Word、参考图等输入素材
work/      # 脚本生成的中间 JSON 和图表资产，本地生成，不提交 GitHub
outputs/   # 最终 PSD / PNG，本地生成，不提交 GitHub
```

## 本周交付口径

本周使用 `金葵花债市周度复盘20260528.docx` 作为原始素材，并生成三版长图文案：

- `债市周观察原版.docx`
- `债市周观察（固收+）.docx`
- `债市周观察（债市）.docx`

主要处理口径：

- 三版仅替换首屏投资建议，主体债市表现、债市分析、后市展望和配置策略保持一致。
- 债市表现一句话压缩为：`5月22日至5月28日，国债收益率全期限下行。`
- 数据来源口径：`wind，截至2026年5月28日`。
- 图表使用 Word 内嵌图表数据生成，后续仍可接入原始 Excel 进一步提升高保真度。

## 核心流程

1. `scripts/generate_week_variant_docs.py`：生成三版 Word 母版。
2. `scripts/extract_word_psd_content.py`：拆解 Word 文案并生成结构化 JSON。
3. `scripts/prepare_native_v3_content.py`：生成 PSD 可消费的文字、标红、布局和资产计划。
4. `scripts/build_native_psd_v3.jsx`：在 Photoshop 中生成原生文本 PSD 和 PNG。
5. `scripts/inspect_native_v3_text_layers.jsx` / `scripts/inspect_native_v3_manual_psds.jsx`：回读 PSD 图层状态，检查可编辑文字、图表和关键层可见性。

## 质量检查

本次提交前已运行：

```bash
python3 -m unittest discover -s tests
```

结果：`Ran 26 tests ... OK`

## 文件管理原则

- GitHub 保存代码、规范、测试、本周说明和必要的小体积素材。
- PSD、最终 PNG、手动备份和 `work/` 中间文件只保留在本地，避免仓库膨胀。
- 下一周制作时优先更新 `scripts/project_paths.py` 中的 `CURRENT_WEEK`，并新增对应的 `weeks/<date_range>/` 目录。
