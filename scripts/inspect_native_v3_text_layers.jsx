/*
 * Inspect editable native_v3 text layers in the generated PSD.
 */

#target photoshop

(function () {
    var psdPath = "/Users/a123/Downloads/债市周观察/债市周观察/weeks/2026-05-25_2026-05-29/outputs/native_v3/金葵花债市周观察20260521_原生文本v3.psd";
    var outPath = "/Users/a123/Downloads/债市周观察/债市周观察/weeks/2026-05-25_2026-05-29/work/native_v3/text_layers.tsv";

    function cleanText(s) {
        if (s === undefined || s === null) {
            return "";
        }
        return String(s).replace(/\r/g, "\\n").replace(/\n/g, "\\n").replace(/\t/g, " ");
    }

    function unitValue(v) {
        try {
            return v.as("px");
        } catch (e) {
            return Number(v);
        }
    }

    function pathContainsNativeV3(path) {
        return path.indexOf("native_v3") >= 0;
    }

    app.displayDialogs = DialogModes.NO;
    var oldUnits = app.preferences.rulerUnits;
    app.preferences.rulerUnits = Units.PIXELS;

    var doc = app.open(new File(psdPath));
    var lines = ["path\tkind\tfont\tsize\tcolor\tbounds\ttext"];

    function walk(container, prefix) {
        for (var i = container.layers.length - 1; i >= 0; i--) {
            var layer = container.layers[i];
            var path = prefix ? prefix + "/" + layer.name : layer.name;
            if (layer.typename === "LayerSet") {
                walk(layer, path);
                continue;
            }

            if (!pathContainsNativeV3(path)) {
                continue;
            }

            var kind = "";
            var fontName = "";
            var size = "";
            var color = "";
            var text = "";
            if (layer.typename === "ArtLayer") {
                try {
                    if (layer.kind === LayerKind.TEXT) {
                        kind = "TEXT";
                        fontName = layer.textItem.font;
                        size = layer.textItem.size;
                        text = layer.textItem.contents;
                        color = [
                            Math.round(layer.textItem.color.rgb.red),
                            Math.round(layer.textItem.color.rgb.green),
                            Math.round(layer.textItem.color.rgb.blue)
                        ].join(",");
                    } else {
                        kind = String(layer.kind);
                    }
                } catch (e1) {}
            }

            var bounds = "";
            try {
                var b = layer.bounds;
                bounds = [
                    unitValue(b[0]),
                    unitValue(b[1]),
                    unitValue(b[2]),
                    unitValue(b[3])
                ].join(",");
            } catch (e2) {}

            lines.push([cleanText(path), cleanText(kind), cleanText(fontName), cleanText(size), cleanText(color), cleanText(bounds), cleanText(text)].join("\t"));
        }
    }

    walk(doc, "");

    var f = new File(outPath);
    f.encoding = "UTF-8";
    f.open("w");
    f.write(lines.join("\n"));
    f.close();

    doc.close(SaveOptions.DONOTSAVECHANGES);
    app.preferences.rulerUnits = oldUnits;
    "wrote " + outPath;
})();
