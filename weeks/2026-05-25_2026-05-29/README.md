# 2026-05-25 至 2026-05-29 制作周

## 目录

```text
inputs/
├── psd/                    # 原始 Photoshop 模板
├── word/
│   ├── raw/                # 原始完整周报 Word
│   ├── edited/             # 修改版/长图母版 Word
│   └── variants/           # 原版、固收+、债市三版 Word
└── reference_long_images/  # 旧版参考长图

work/                       # 脚本生成的中间文件，可重新生成
outputs/
├── 20260521新版/           # 第一轮 overlay 方案，已不作为主路线
├── basic_v0/               # 重画组件实验，已不作为主路线
├── native_v1/              # PSD 原生组件替换实验
├── native_v2/              # 富文本图片修正版，视觉验证用
└── native_v3/              # 当前主路线：可编辑 PSD 原生文本
```

## 当前主线

- 内容来源：`inputs/word/variants/债市周观察原版.docx`
- 结构化内容：`work/psd_content/原版.json`
- Photoshop 输入：`work/native_v3/content.json`
- 原版输出：`outputs/native_v3/金葵花债市周观察20260521_原生文本v3.png`
- 原版 PSD：`outputs/native_v3/金葵花债市周观察20260521_原生文本v3.psd`
- PSD 正文层：`75` 个 Photoshop `TEXT` 图层，字体 `SourceHanSansCN-Medium`

## 当前结论

- `native_v1` 证明了复用原 PSD 组件比重画卡片更接近原版。
- `native_v2` 解决了透明图表、红字和文本裁切，但红字段落是图片，不满足最终可编辑要求。
- `native_v3` 已把红黑正文升级为可编辑文字层，是后续继续打磨的基线。
- 图表和表格仍是图片层，后续需要继续优化视觉样式。
- 整体高度仍沿用原 PSD 固定高度，后续需要做真实自适应。

## 备注

项目通用脚本、schema 和文档仍在根目录：

- `scripts/`
- `schemas/`
- `docs/`

当前制作周由 `scripts/project_paths.py` 控制。
