/*
 * Native PSD component replacement v3.
 * Keeps the original PSD components and renders rich paragraphs as editable
 * Photoshop text layers instead of rasterized text images.
 */

#target photoshop

(function () {
    var JSON_PATH = "/Users/a123/Downloads/债市周观察/债市周观察/weeks/2026-05-25_2026-05-29/work/native_v3/content.json";

    function readText(path) {
        var file = new File(path);
        if (!file.exists) {
            throw new Error("Missing file: " + path);
        }
        file.encoding = "UTF-8";
        file.open("r");
        var text = file.read();
        file.close();
        return text;
    }

    function readJson(path) {
        return eval("(" + readText(path) + ")");
    }

    function px(value) {
        return value.as("px");
    }

    function makeColor(rgb) {
        var color = new SolidColor();
        color.rgb.red = rgb[0];
        color.rgb.green = rgb[1];
        color.rgb.blue = rgb[2];
        return color;
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

    function findTextLayerByPrefix(doc, prefix) {
        var found = null;
        walk(doc, function (layer) {
            if (found !== null) {
                return;
            }
            var text = layerText(layer);
            if (text.indexOf(prefix) === 0) {
                found = layer;
            }
        });
        return found;
    }

    function findTextLayerContaining(doc, needle) {
        var found = null;
        walk(doc, function (layer) {
            if (found !== null) {
                return;
            }
            var text = layerText(layer);
            if (text.indexOf(needle) >= 0) {
                found = layer;
            }
        });
        return found;
    }

    function findTextLayerByMatch(doc, match) {
        if (match.type === "contains") {
            return findTextLayerContaining(doc, match.text);
        }
        return findTextLayerByPrefix(doc, match.text);
    }

    function setTextByExact(doc, oldText, newText, label) {
        var layer = findTextLayerByPrefix(doc, oldText);
        if (layer === null || layerText(layer) !== oldText) {
            throw new Error("Cannot find exact text layer: " + label + " / " + oldText);
        }
        layer.textItem.contents = newText;
        layer.name = label;
        return layer;
    }

    function setTextByPrefix(doc, oldPrefix, newText, label) {
        var layer = findTextLayerByPrefix(doc, oldPrefix);
        if (layer === null) {
            throw new Error("Cannot find text layer: " + label + " / " + oldPrefix);
        }
        layer.textItem.contents = newText;
        layer.name = label;
        return layer;
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
        var scaleX = box.width / b1.width * 100;
        var scaleY = box.height / b1.height * 100;
        layer.resize(scaleX, scaleY, AnchorPosition.TOPLEFT);
        moveLayerTo(layer, box.left, box.top);
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

    function placeImageIntoBounds(doc, imagePath, targetLayerName, newLayerName) {
        var target = findLayerByName(doc, targetLayerName);
        if (target === null) {
            throw new Error("Cannot find target image layer: " + targetLayerName);
        }
        var box = boundsOf(target);
        target.visible = false;
        return pasteImageIntoBounds(doc, imagePath, box, newLayerName, target);
    }

    function trySetFont(textItem, preferred) {
        var candidates = [
            preferred,
            "SourceHanSansCN-Medium",
            "SourceHanSansCN-Regular",
            "PingFangSC-Semibold",
            "PingFangSC-Regular",
            "STHeitiSC-Medium"
        ];
        for (var i = 0; i < candidates.length; i++) {
            try {
                textItem.font = candidates[i];
                return candidates[i];
            } catch (e) {
                // Try the next installed font.
            }
        }
        return "";
    }

    function moveIntoGroup(layer, group) {
        try {
            layer.move(group, ElementPlacement.INSIDE);
        } catch (e) {
            try {
                layer.move(group, ElementPlacement.PLACEATBEGINNING);
            } catch (ignored) {}
        }
    }

    function createTextRun(doc, group, blockKey, runIndex, run, left, top) {
        app.activeDocument = doc;
        var layer = doc.artLayers.add();
        layer.kind = LayerKind.TEXT;
        layer.name = "native_v3/" + blockKey + "/" + ("000" + runIndex).slice(-3);

        var textItem = layer.textItem;
        textItem.kind = TextType.POINTTEXT;
        textItem.contents = run.text;
        textItem.size = run.size;
        textItem.leading = run.leading;
        textItem.color = makeColor(run.color);
        trySetFont(textItem, run.font);
        textItem.position = [left + run.x, top + run.y];
        moveIntoGroup(layer, group);
    }

    function renderNativeTextBlock(doc, blockKey, block) {
        var target = findTextLayerByMatch(doc, block.match);
        if (target === null) {
            throw new Error("Cannot find text target for block: " + blockKey + " / " + block.match.text);
        }
        var box = boundsOf(target);
        target.visible = false;

        var group = doc.layerSets.add();
        group.name = "native_v3_text_" + blockKey;
        try {
            group.move(target, ElementPlacement.PLACEBEFORE);
        } catch (e) {}

        for (var i = 0; i < block.runs.length; i++) {
            createTextRun(doc, group, blockKey, i + 1, block.runs[i], box.left, box.top);
        }
    }

    function savePsd(doc, path) {
        var file = new File(path);
        var opts = new PhotoshopSaveOptions();
        opts.layers = true;
        opts.alphaChannels = true;
        opts.annotations = true;
        opts.embedColorProfile = true;
        doc.saveAs(file, opts, true, Extension.LOWERCASE);
    }

    function exportPreview(doc, data) {
        var preview = doc.duplicate("native_v3_preview", true);
        app.activeDocument = preview;
        preview.crop([data.x0, 0, data.x0 + data.width, data.height]);
        preview.saveAs(new File(data.output_png), new PNGSaveOptions(), true, Extension.LOWERCASE);
        preview.close(SaveOptions.DONOTSAVECHANGES);
        app.activeDocument = doc;
    }

    app.displayDialogs = DialogModes.NO;
    var oldUnits = app.preferences.rulerUnits;
    app.preferences.rulerUnits = Units.PIXELS;

    try {
        var data = readJson(JSON_PATH);
        var doc = app.open(new File(data.original_psd));

        setTextByExact(doc, "2026-5-18", data.date, "日期_2026-5-21");
        setTextByExact(doc, "国债收益率窄幅震荡，曲线走平", data.top_title, "首屏标题_国债收益率整体下行");
        setTextByPrefix(doc, "数据来源：wind", data.source_risk, "数据来源及风险提示_原生替换");

        renderNativeTextBlock(doc, "top_intro", data.native_text_blocks.top_intro);
        renderNativeTextBlock(doc, "market_sentence", data.native_text_blocks.market_sentence);
        renderNativeTextBlock(doc, "funding", data.native_text_blocks.funding);
        renderNativeTextBlock(doc, "fund_chart_title", data.native_text_blocks.fund_chart_title);
        renderNativeTextBlock(doc, "risk_preference", data.native_text_blocks.risk_preference);
        renderNativeTextBlock(doc, "outlook", data.native_text_blocks.outlook);
        renderNativeTextBlock(doc, "strategy", data.native_text_blocks.strategy);

        placeImageIntoBounds(doc, data.assets.table, "表1", "表1_20260521_原生替换");
        placeImageIntoBounds(doc, data.assets.yield_chart, "图片1", "图片1_国债收益率曲线_透明v3");
        placeImageIntoBounds(doc, data.assets.fund_chart, "图片2", "图片2_资金利率曲线_透明v3");

        savePsd(doc, data.output_psd);
        exportPreview(doc, data);
        doc.close(SaveOptions.DONOTSAVECHANGES);
    } finally {
        app.preferences.rulerUnits = oldUnits;
    }
})();
