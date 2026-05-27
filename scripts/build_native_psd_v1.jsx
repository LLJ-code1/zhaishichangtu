/*
 * Native PSD component replacement v1.
 * Keeps the original PSD cards, title bars, icons, filters, and shadows.
 * Replaces only text contents and table/chart image layers.
 */

#target photoshop

(function () {
    var JSON_PATH = "/Users/a123/Downloads/债市周观察/债市周观察/weeks/2026-05-25_2026-05-29/work/native_v1/content.json";

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

    function setTextByPrefix(doc, oldPrefix, newText, label) {
        var layer = findTextLayerByPrefix(doc, oldPrefix);
        if (layer === null) {
            throw new Error("Cannot find text layer: " + label + " / " + oldPrefix);
        }
        layer.textItem.contents = newText;
        layer.name = label;
        return layer;
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

    function setTextByContains(doc, needle, newText, label) {
        var layer = findTextLayerContaining(doc, needle);
        if (layer === null) {
            throw new Error("Cannot find text layer containing: " + label + " / " + needle);
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

    function placeImageIntoBounds(doc, imagePath, targetLayerName, newLayerName) {
        var target = findLayerByName(doc, targetLayerName);
        if (target === null) {
            throw new Error("Cannot find target image layer: " + targetLayerName);
        }
        var box = boundsOf(target);
        target.visible = false;

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
        var preview = doc.duplicate("native_v1_preview", true);
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
        setTextByPrefix(doc, "上周债券收益率窄幅震荡", data.intro, "首屏摘要_原生替换");
        setTextByPrefix(doc, "5月8日-5月14日", data.performance_sentence, "债市表现一句话_原生替换");
        setTextByPrefix(doc, "1、央行在公开市场操作上净回笼500亿元", data.funding, "资金面正文_原生替换");
        setTextByPrefix(doc, "DR001/DR007上周情况", data.fund_chart_title, "资金图标题_原生替换");
        setTextByPrefix(doc, "1、特朗普访华落地", data.risk_preference, "市场风险偏好正文_原生替换");
        setTextByPrefix(doc, "展望后市，重点关注特朗普访华进展", data.outlook, "后市展望正文_原生替换");
        setTextByPrefix(doc, "数据来源：wind", data.source_risk, "数据来源及风险提示_原生替换");

        placeImageIntoBounds(doc, data.assets.table, "表1", "表1_20260521_原生替换");
        placeImageIntoBounds(doc, data.assets.yield_chart, "图片1", "图片1_国债收益率曲线_原生替换");
        placeImageIntoBounds(doc, data.assets.fund_chart, "图片2", "图片2_资金利率曲线_原生替换");

        savePsd(doc, data.output_psd);
        exportPreview(doc, data);
        doc.close(SaveOptions.DONOTSAVECHANGES);
    } finally {
        app.preferences.rulerUnits = oldUnits;
    }
})();
