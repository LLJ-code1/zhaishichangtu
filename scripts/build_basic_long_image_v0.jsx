/*
 * Build the basic v0 Photoshop long image from prepared component assets.
 * Run from Photoshop: File > Scripts > Browse...
 */

#target photoshop

(function () {
    var JSON_PATH = "/Users/a123/Downloads/债市周观察/债市周观察/weeks/2026-05-25_2026-05-29/work/basic_v0/content.json";

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

    function trySetFont(textItem) {
        var candidates = [
            "STHeitiSC-Medium",
            "PingFangSC-Semibold",
            "PingFangSC-Regular",
            "SongtiSC-Regular"
        ];
        for (var i = 0; i < candidates.length; i++) {
            try {
                textItem.font = candidates[i];
                return;
            } catch (e) {
                // Try the next installed font.
            }
        }
    }

    function moveLayerTo(layer, x, y) {
        var b = layer.bounds;
        layer.translate(x - px(b[0]), y - px(b[1]));
    }

    function moveIntoGroup(layer, group) {
        try {
            layer.move(group, ElementPlacement.INSIDE);
        } catch (e) {
            try {
                layer.move(group, ElementPlacement.PLACEATBEGINNING);
            } catch (ignored) {
                // Grouping is useful for inspection, but failed grouping should not stop output.
            }
        }
    }

    function hideOldRightBody(container, x0, width, finalHeight) {
        for (var i = container.layers.length - 1; i >= 0; i--) {
            var layer = container.layers[i];
            if (layer.typename === "LayerSet") {
                hideOldRightBody(layer, x0, width, finalHeight);
                continue;
            }
            try {
                var b = layer.bounds;
                var left = px(b[0]);
                var top = px(b[1]);
                var right = px(b[2]);
                var bottom = px(b[3]);
                var intersectsRightColumn = right > x0 && left < x0 + width;
                var isBodyLayer = top >= 490 && top < finalHeight + 150 && bottom > 500;
                if (intersectsRightColumn && isBodyLayer) {
                    layer.visible = false;
                }
            } catch (e) {
                // Some adjustment or empty layers have no usable bounds.
            }
        }
    }

    function placeImage(baseDoc, group, data, item) {
        var file = new File(item.path);
        if (!file.exists) {
            throw new Error("Missing image asset: " + item.path);
        }

        var assetDoc = app.open(file);
        assetDoc.selection.selectAll();
        assetDoc.selection.copy();
        assetDoc.close(SaveOptions.DONOTSAVECHANGES);

        app.activeDocument = baseDoc;
        var layer = baseDoc.paste();
        layer.name = item.section + " / " + item.name;
        moveLayerTo(layer, data.x0 + item.x, item.y);
        moveIntoGroup(layer, group);
    }

    function addText(baseDoc, group, data, item) {
        app.activeDocument = baseDoc;
        var layer = baseDoc.artLayers.add();
        layer.kind = LayerKind.TEXT;
        layer.name = item.section + " / " + item.name;

        var textItem = layer.textItem;
        textItem.kind = TextType.POINTTEXT;
        textItem.contents = item.text;
        textItem.size = item.size;
        textItem.color = makeColor(item.color);
        trySetFont(textItem);
        textItem.position = [data.x0 + item.x, item.y + Math.round(item.size * 0.92)];
        moveIntoGroup(layer, group);
    }

    function savePsd(doc, path) {
        var file = new File(path);
        var opts = new PhotoshopSaveOptions();
        opts.layers = true;
        doc.saveAs(file, opts, true, Extension.LOWERCASE);
    }

    function exportPreview(doc, data) {
        var preview = doc.duplicate("basic_v0_preview", true);
        app.activeDocument = preview;
        preview.crop([data.x0, 0, data.x0 + data.width, data.final_height]);
        var out = new File(data.output_png);
        var pngOpts = new PNGSaveOptions();
        preview.saveAs(out, pngOpts, true, Extension.LOWERCASE);
        preview.close(SaveOptions.DONOTSAVECHANGES);
        app.activeDocument = doc;
    }

    app.displayDialogs = DialogModes.NO;
    var oldUnits = app.preferences.rulerUnits;
    app.preferences.rulerUnits = Units.PIXELS;

    try {
        var data = readJson(JSON_PATH);
        var doc = app.open(new File(data.original_psd));

        hideOldRightBody(doc, data.x0, data.width, data.final_height);

        var group = doc.layerSets.add();
        group.name = "基础长图v0_主体";

        for (var i = 0; i < data.layers.length; i++) {
            var item = data.layers[i];
            if (item.type === "image") {
                placeImage(doc, group, data, item);
            } else if (item.type === "text") {
                addText(doc, group, data, item);
            }
        }

        savePsd(doc, data.output_psd);
        exportPreview(doc, data);
        doc.close(SaveOptions.DONOTSAVECHANGES);
    } finally {
        app.preferences.rulerUnits = oldUnits;
    }
})();
