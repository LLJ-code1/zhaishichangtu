/*
 * Inspect relevant layers in the three manually edited native_v3 PSDs.
 */

#target photoshop

(function () {
    var outPath = "/Users/a123/Downloads/债市周观察/债市周观察/weeks/2026-06-01_2026-06-05/work/native_v3/manual_psd_layers.tsv";
    var psdPaths = [
        "/Users/a123/Downloads/债市周观察/债市周观察/weeks/2026-06-01_2026-06-05/outputs/native_v3/金葵花债市周观察20260528_原版_原生文本v3.psd",
        "/Users/a123/Downloads/债市周观察/债市周观察/weeks/2026-06-01_2026-06-05/outputs/native_v3/金葵花债市周观察20260528_固收+_原生文本v3.psd",
        "/Users/a123/Downloads/债市周观察/债市周观察/weeks/2026-06-01_2026-06-05/outputs/native_v3/金葵花债市周观察20260528_债市_原生文本v3.psd"
    ];

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

    function boundsText(layer) {
        try {
            var b = layer.bounds;
            return [
                unitValue(b[0]),
                unitValue(b[1]),
                unitValue(b[2]),
                unitValue(b[3])
            ].join(",");
        } catch (e) {}
        return "";
    }

    function layerText(layer) {
        try {
            if (layer.typename === "ArtLayer" && layer.kind === LayerKind.TEXT) {
                return layer.textItem.contents;
            }
        } catch (e) {}
        return "";
    }

    function shouldRecord(path, layer) {
        var text = layerText(layer);
        return path.indexOf("native_v3_rich_text_outlook") >= 0 ||
            path.indexOf("native_v3_rich_text_strategy") >= 0 ||
            path.indexOf("图片2") >= 0 ||
            path.indexOf("DR001") >= 0 ||
            /^2026-\d{1,2}-\d{1,2}$/.test(text) ||
            text.indexOf("长端") >= 0 ||
            text.indexOf("DR001") >= 0;
    }

    function walk(container, prefix, rows, variant) {
        for (var i = container.layers.length - 1; i >= 0; i--) {
            var layer = container.layers[i];
            var path = prefix ? prefix + "/" + layer.name : layer.name;
            if (shouldRecord(path, layer)) {
                rows.push([
                    variant,
                    cleanText(path),
                    cleanText(layer.typename),
                    String(layer.visible),
                    cleanText(boundsText(layer)),
                    cleanText(layerText(layer))
                ].join("\t"));
            }
            if (layer.typename === "LayerSet") {
                walk(layer, path, rows, variant);
            }
        }
    }

    function variantFromPath(path) {
        if (path.indexOf("_固收+_") >= 0) {
            return "固收+";
        }
        if (path.indexOf("_债市_") >= 0) {
            return "债市";
        }
        return "原版";
    }

    app.displayDialogs = DialogModes.NO;
    var oldUnits = app.preferences.rulerUnits;
    app.preferences.rulerUnits = Units.PIXELS;

    var rows = ["variant\tpath\tkind\tvisible\tbounds\ttext"];
    for (var p = 0; p < psdPaths.length; p++) {
        var doc = app.open(new File(psdPaths[p]));
        walk(doc, "", rows, variantFromPath(psdPaths[p]));
        doc.close(SaveOptions.DONOTSAVECHANGES);
    }

    var out = new File(outPath);
    out.encoding = "UTF-8";
    out.lineFeed = "Unix";
    out.open("w");
    out.write(rows.join("\n"));
    out.close();
    app.preferences.rulerUnits = oldUnits;
    "wrote " + outPath;
})();
