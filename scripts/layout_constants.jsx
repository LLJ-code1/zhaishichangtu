/**
 * layout_constants.jsx
 * 所有排版常量集中定义，禁止在其他文件中写 magic number。
 * 修改间距只改这里，不改其他文件。
 */

// ===== 画布 =====
var CANVAS_WIDTH         = 1125;
var CONTENT_LEFT         = 88;
var CONTENT_RIGHT        = 1037;
var CONTENT_WIDTH        = 930;   // CONTENT_RIGHT - CONTENT_LEFT 近似

// ===== section 间距 =====
var SECTION_GAP          = 32;    // section 之间
var HEADER_TO_CARD_GAP   = 12;    // 标题条到卡片
var CARD_PADDING_TOP     = 45;    // 卡片内顶部
var CARD_PADDING_BOTTOM  = 45;    // 卡片内底部
var COMPONENT_GAP        = 24;    // 卡片内组件之间
var FOOTER_MARGIN        = 60;    // 最底部

// ===== 文字 =====
var BODY_FONT_SIZE       = 33;
var BODY_LEADING         = 54;    // 约 1.35x
var SUBTITLE_FONT_SIZE   = 35;
var TITLE_FONT_SIZE      = 40;
var LABEL_FONT_SIZE      = 31;
var DISCLAIMER_FONT_SIZE = 25;

// ===== 字体名（PostScript name，按你 PS 中实际可用字体调整）=====
var FONT_HEITI           = "STHeitiSC-Medium";
var FONT_SONG            = "STSongti-SC-Regular";

// ===== 颜色 =====
var COLOR_BLACK          = [24, 22, 20];
var COLOR_RED            = [232, 31, 31];
var COLOR_GREY           = [110, 110, 110];
var COLOR_GOLD           = [214, 155, 71];
var COLOR_CREAM          = [255, 248, 235];
var COLOR_CREAM2         = [255, 251, 243];
var COLOR_WHITE          = [255, 255, 255];

// ===== 债市分析分栏 =====
var ICON_COLUMN_WIDTH    = 260;
var ICON_TEXT_GAP         = 30;
var ANALYSIS_TEXT_LEFT    = CONTENT_LEFT + ICON_COLUMN_WIDTH + ICON_TEXT_GAP;  // 378
var ANALYSIS_TEXT_WIDTH   = CONTENT_RIGHT - ANALYSIS_TEXT_LEFT;                // 659

// ===== 图片资产宽度 =====
var TABLE_IMG_WIDTH      = 900;
var CHART_YIELD_WIDTH    = 860;
var CHART_FUND_WIDTH     = 770;

// ===== 校验阈值 =====
var MAX_ALLOWED_GAP      = 80;    // 两组件间距超过此值视为异常留白
var MIN_TOTAL_HEIGHT     = 5500;  // 长图最小高度（低于此值说明内容缺失）
var MAX_TOTAL_HEIGHT     = 8500;  // 长图最大高度（超过此值说明有异常撑开）


// ===== 工具函数 =====

/** 测量图层实际像素高度 */
function measureLayerHeight(layer) {
    var b = layer.bounds;
    return b[3].as("px") - b[1].as("px");
}

/** 测量图层底部 y 坐标 */
function measureLayerBottom(layer) {
    return layer.bounds[3].as("px");
}

/** 测量图层顶部 y 坐标 */
function measureLayerTop(layer) {
    return layer.bounds[1].as("px");
}

/** 检查两个图层是否垂直重叠 */
function checkOverlap(layerA, layerB) {
    var aBottom = layerA.bounds[3].as("px");
    var bTop = layerB.bounds[1].as("px");
    return bTop < aBottom;
}
