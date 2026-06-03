/*
 * List visible layers from the current native_v3 output PSD.
 */

#target photoshop

(function () {
    var psdPath = "/Users/a123/Downloads/债市周观察/债市周观察/weeks/2026-06-01_2026-06-05/outputs/native_v3/金葵花债市周观察20260528_原版_原生文本v3.psd";
    var outPath = "/Users/a123/Downloads/债市周观察/债市周观察/weeks/2026-06-01_2026-06-05/work/native_v3/output_layers.tsv";

    function px(value) {
        return value.as("px");
    }

    function cleanText(value) {
        return String(value || "").replace(/\r/g, "\\n").replace(/\n/g, "\\n").replace(/\t/g, " ");
    }

    app.displayDialogs = DialogModes.NO;
    var doc = app.open(new File(psdPath));
    var lines = ["depth\tpath\tkind\tvisible\tbounds\ttext"];

    function walk(container, prefix, depth) {
        for (var i = container.layers.length - 1; i >= 0; i--) {
            var layer = container.layers[i];
            var layerPath = prefix ? prefix + "/" + layer.name : layer.name;
            var boundsText = "";
            try {
                boundsText = [
                    px(layer.bounds[0]),
                    px(layer.bounds[1]),
                    px(layer.bounds[2]),
                    px(layer.bounds[3])
                ].join(",");
            } catch (e1) {}

            var text = "";
            try {
                if (layer.typename === "ArtLayer" && layer.kind === LayerKind.TEXT) {
                    text = layer.textItem.contents;
                }
            } catch (e2) {}

            var row = String(depth) + "\t" +
                cleanText(layerPath) + "\t" +
                cleanText(layer.typename) + "\t" +
                String(layer.visible) + "\t" +
                boundsText + "\t" +
                cleanText(text);
            lines.push(row);
            if (layer.typename === "LayerSet") {
                walk(layer, layerPath, depth + 1);
            }
        }
    }

    walk(doc, "", 0);

    var out = new File(outPath);
    out.encoding = "UTF-8";
    out.open("w");
    out.write(lines.join("\n"));
    out.close();
    doc.close(SaveOptions.DONOTSAVECHANGES);
})();
