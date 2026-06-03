/*
 * Apply final manual PSD touches without regenerating from template:
 * - unify outlook emphasis phrases with the existing red text style
 * - replace funding chart with an aligned transparent asset matching the yield chart style
 * - export updated cropped PNG previews
 */

#target photoshop

(function () {
    var X0 = 3042;
    var WIDTH = 1125;
    var HEIGHT = 6893;
    var CHART_ASSET = "/Users/a123/Downloads/债市周观察/债市周观察/weeks/2026-06-01_2026-06-05/work/native_v3/assets/fund_chart_aligned.png";
    var BLACK = [24, 22, 20];
    var RED = [232, 31, 31];
    var ITEMS = [
        {
            psd: "/Users/a123/Downloads/债市周观察/债市周观察/weeks/2026-06-01_2026-06-05/outputs/native_v3/金葵花债市周观察20260528_原版_原生文本v3.psd",
            png: "/Users/a123/Downloads/债市周观察/债市周观察/weeks/2026-06-01_2026-06-05/outputs/native_v3/金葵花债市周观察20260528_原版_原生文本v3.png"
        },
        {
            psd: "/Users/a123/Downloads/债市周观察/债市周观察/weeks/2026-06-01_2026-06-05/outputs/native_v3/金葵花债市周观察20260528_固收+_原生文本v3.psd",
            png: "/Users/a123/Downloads/债市周观察/债市周观察/weeks/2026-06-01_2026-06-05/outputs/native_v3/金葵花债市周观察20260528_固收+_原生文本v3.png"
        },
        {
            psd: "/Users/a123/Downloads/债市周观察/债市周观察/weeks/2026-06-01_2026-06-05/outputs/native_v3/金葵花债市周观察20260528_债市_原生文本v3.psd",
            png: "/Users/a123/Downloads/债市周观察/债市周观察/weeks/2026-06-01_2026-06-05/outputs/native_v3/金葵花债市周观察20260528_债市_原生文本v3.png"
        }
    ];
    var OUTLOOK_RED_PHRASES = [
        "债市依旧处于多头趋势之中",
        "配置盘依旧欠配",
        "交易盘积极转多",
        "关注长端超额下行空间"
    ];

    function px(value) {
        return value.as("px");
    }

    function boundsOf(layer) {
        var b = layer.bounds;
        return {
            left: px(b[0]),
            top: px(b[1]),
            right: px(b[2]),
            bottom: px(b[3]),
            width: px(b[2]) - px(b[0]),
            height: px(b[3]) - px(b[1])
        };
    }

    function moveLayerTo(layer, x, y) {
        var b = layer.bounds;
        layer.translate(x - px(b[0]), y - px(b[1]));
    }

    function fitLayerToBounds(layer, box) {
        moveLayerTo(layer, box.left, box.top);
        var b1 = boundsOf(layer);
        layer.resize(box.width / b1.width * 100, box.height / b1.height * 100, AnchorPosition.TOPLEFT);
        moveLayerTo(layer, box.left, box.top);
    }

    function layerText(layer) {
        try {
            if (layer.typename === "ArtLayer" && layer.kind === LayerKind.TEXT) {
                return String(layer.textItem.contents);
            }
        } catch (e) {}
        return "";
    }

    function walk(container, callback) {
        for (var i = container.layers.length - 1; i >= 0; i--) {
            var layer = container.layers[i];
            callback(layer);
            if (layer.typename === "LayerSet") {
                walk(layer, callback);
            }
        }
    }

    function findLayerByName(doc, name) {
        var found = null;
        walk(doc, function (layer) {
            if (found === null && layer.name === name) {
                found = layer;
            }
        });
        return found;
    }

    function findTextLayerContaining(doc, text, minTop, maxTop) {
        var found = null;
        walk(doc, function (layer) {
            if (found !== null || layer.typename !== "ArtLayer" || !layer.visible) {
                return;
            }
            if (layerText(layer).indexOf(text) < 0) {
                return;
            }
            var box = boundsOf(layer);
            if (box.top >= minTop && box.top <= maxTop) {
                found = layer;
            }
        });
        return found;
    }

    function setTopDate(doc, dateText) {
        var found = null;
        walk(doc, function (layer) {
            if (found !== null || layer.typename !== "ArtLayer" || !layer.visible) {
                return;
            }
            var text = layerText(layer);
            if (!/^2026-\d{1,2}-\d{1,2}$/.test(text)) {
                return;
            }
            var box = boundsOf(layer);
            if (box.top >= 300 && box.top <= 430) {
                found = layer;
            }
        });
        if (found === null) {
            throw new Error("Cannot find top date layer.");
        }
        found.textItem.contents = dateText;
    }

    function findTextLayerAnyVisibility(doc, text) {
        var found = null;
        walk(doc, function (layer) {
            if (found === null && layerText(layer).indexOf(text) >= 0) {
                found = layer;
            }
        });
        return found;
    }

    function findFundingTitleLayer(doc) {
        var named = findLayerByName(doc, "native_v3_rich_text_fund_chart_title");
        if (named !== null) {
            return named;
        }
        var ranged = null;
        walk(doc, function (layer) {
            if (layer.typename !== "ArtLayer") {
                return;
            }
            if (layerText(layer).indexOf("DR001/DR007上周情况") < 0) {
                return;
            }
            var box = boundsOf(layer);
            if (box.top >= 3600 && box.top <= 3900) {
                if (ranged === null) {
                    ranged = layer;
                }
            }
        });
        return ranged || findTextLayerAnyVisibility(doc, "DR001/DR007上周情况");
    }

    function normalizeFundingTitleVisibility(doc, title) {
        walk(doc, function (layer) {
            if (layerText(layer).indexOf("DR001/DR007上周情况") >= 0) {
                layer.visible = layer === title;
            }
        });
    }

    function rgbDescriptor(rgb) {
        var desc = new ActionDescriptor();
        desc.putDouble(charIDToTypeID("Rd  "), rgb[0]);
        desc.putDouble(charIDToTypeID("Grn "), rgb[1]);
        desc.putDouble(charIDToTypeID("Bl  "), rgb[2]);
        return desc;
    }

    function currentTextKey() {
        var ref = new ActionReference();
        ref.putProperty(charIDToTypeID("Prpr"), charIDToTypeID("Txt "));
        ref.putEnumerated(charIDToTypeID("Lyr "), charIDToTypeID("Ordn"), charIDToTypeID("Trgt"));
        return executeActionGet(ref).getObjectValue(charIDToTypeID("Txt "));
    }

    function applyUnifiedTextStyle(styleDesc, rgb) {
        styleDesc.putObject(charIDToTypeID("Clr "), charIDToTypeID("RGBC"), rgbDescriptor(rgb));
        try {
            styleDesc.putString(stringIDToTypeID("fontPostScriptName"), "SourceHanSansCN-Medium");
            styleDesc.putString(stringIDToTypeID("fontName"), "Source Han Sans CN");
            styleDesc.putString(stringIDToTypeID("fontStyleName"), "Medium");
        } catch (e1) {}
        try {
            styleDesc.putBoolean(stringIDToTypeID("syntheticBold"), false);
        } catch (e2) {}
    }

    function unifyRedOutlookLayer(doc, layer) {
        app.activeDocument = doc;
        doc.activeLayer = layer;
        var text = layerText(layer);
        var marks = [];
        for (var i = 0; i < OUTLOOK_RED_PHRASES.length; i++) {
            var phrase = OUTLOOK_RED_PHRASES[i];
            var idx = text.indexOf(phrase);
            if (idx >= 0) {
                marks.push({ from: idx, to: idx + phrase.length, bold: true });
            }
        }
        if (marks.length === 0) {
            throw new Error("No outlook emphasis phrases found.");
        }
        marks.sort(function (a, b) { return a.from - b.from; });

        var textKey = currentTextKey();
        var existingRanges = textKey.getList(charIDToTypeID("Txtt"));
        var styleRanges = new ActionList();
        var cursor = 0;

        function pushRange(from, to, rgb, bold) {
            if (to <= from) {
                return;
            }
            var rangeDesc = new ActionDescriptor();
            rangeDesc.putInteger(charIDToTypeID("From"), from);
            rangeDesc.putInteger(charIDToTypeID("T   "), to);
            var styleDesc = existingRanges.getObjectValue(0).getObjectValue(charIDToTypeID("TxtS"));
            applyUnifiedTextStyle(styleDesc, rgb);
            rangeDesc.putObject(charIDToTypeID("TxtS"), charIDToTypeID("TxtS"), styleDesc);
            styleRanges.putObject(charIDToTypeID("Txtt"), rangeDesc);
        }

        for (var j = 0; j < marks.length; j++) {
            var mark = marks[j];
            pushRange(cursor, mark.from, BLACK, false);
            pushRange(mark.from, mark.to, RED, false);
            cursor = mark.to;
        }
        pushRange(cursor, text.length, BLACK, false);
        textKey.putList(charIDToTypeID("Txtt"), styleRanges);

        var setDesc = new ActionDescriptor();
        var ref = new ActionReference();
        ref.putEnumerated(charIDToTypeID("TxLr"), charIDToTypeID("Ordn"), charIDToTypeID("Trgt"));
        setDesc.putReference(charIDToTypeID("null"), ref);
        setDesc.putObject(charIDToTypeID("T   "), charIDToTypeID("TxLr"), textKey);
        executeAction(charIDToTypeID("setd"), setDesc, DialogModes.NO);
    }

    function pasteImageIntoBounds(doc, imagePath, box, newLayerName, target) {
        var asset = app.open(new File(imagePath));
        asset.selection.selectAll();
        asset.selection.copy();
        asset.close(SaveOptions.DONOTSAVECHANGES);

        app.activeDocument = doc;
        var pasted = doc.paste();
        pasted.name = newLayerName;
        fitLayerToBounds(pasted, box);
        try {
            pasted.move(target, ElementPlacement.PLACEBEFORE);
        } catch (e) {}
        return pasted;
    }

    function replaceFundingChartWithAlignedAsset(doc) {
        var oldChart = findLayerByName(doc, "图片2_资金利率曲线_透明v3");
        var yieldChart = findLayerByName(doc, "图片1_国债收益率曲线_透明v3");
        var title = findFundingTitleLayer(doc);
        if (oldChart === null || title === null) {
            throw new Error("Cannot find funding chart or title layer.");
        }

        var existing = findLayerByName(doc, "图片2_Word样式资金图_20260601");
        if (existing !== null) {
            existing.visible = false;
        }
        var existingAligned = findLayerByName(doc, "图片2_资金利率曲线_透明对齐v4");
        if (existingAligned !== null) {
            existingAligned.remove();
        }

        oldChart.visible = false;
        title.visible = true;
        normalizeFundingTitleVisibility(doc, title);

        var chartBox = boundsOf(oldChart);
        var alignBox = yieldChart === null ? chartBox : boundsOf(yieldChart);
        pasteImageIntoBounds(doc, CHART_ASSET, {
            left: alignBox.left,
            top: chartBox.top,
            right: alignBox.right,
            bottom: chartBox.bottom,
            width: alignBox.right - alignBox.left,
            height: chartBox.bottom - chartBox.top
        }, "图片2_资金利率曲线_透明对齐v4", oldChart);
    }

    function exportPreview(doc, pngPath) {
        var preview = doc.duplicate("native_v3_manual_preview", true);
        app.activeDocument = preview;
        preview.crop([X0, 0, X0 + WIDTH, HEIGHT]);
        preview.saveAs(new File(pngPath), new PNGSaveOptions(), true, Extension.LOWERCASE);
        preview.close(SaveOptions.DONOTSAVECHANGES);
        app.activeDocument = doc;
    }

    app.displayDialogs = DialogModes.NO;
    var oldUnits = app.preferences.rulerUnits;
    app.preferences.rulerUnits = Units.PIXELS;

    try {
        for (var itemIndex = 0; itemIndex < ITEMS.length; itemIndex++) {
            var item = ITEMS[itemIndex];
            var doc = app.open(new File(item.psd));
            var outlook = findTextLayerContaining(doc, "关注长端超额下行空间", 4800, 5300);
            if (outlook === null) {
                throw new Error("Cannot find visible outlook layer in " + item.psd);
            }
            setTopDate(doc, "2026-6-01");
            unifyRedOutlookLayer(doc, outlook);
            replaceFundingChartWithAlignedAsset(doc);
            doc.save();
            exportPreview(doc, item.png);
            doc.close(SaveOptions.DONOTSAVECHANGES);
        }
    } finally {
        app.preferences.rulerUnits = oldUnits;
    }
})();
