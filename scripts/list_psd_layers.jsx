var psdPath = "/Users/a123/Downloads/债市周观察/债市周观察/weeks/2026-05-25_2026-05-29/inputs/psd/债市周报.psd";
var outPath = "/Users/a123/Downloads/债市周观察/债市周观察/psd_layers.tsv";

app.displayDialogs = DialogModes.NO;
var doc = app.open(new File(psdPath));

function cleanText(s) {
  if (s === undefined || s === null) return "";
  return String(s).replace(/\r/g, "\\n").replace(/\n/g, "\\n").replace(/\t/g, " ");
}

function unitValue(v) {
  try { return v.as("px"); } catch (e) { return Number(v); }
}

var lines = ["depth\tpath\tkind\tvisible\tbounds\ttext"];

function walk(container, prefix, depth) {
  for (var i = container.layers.length - 1; i >= 0; i--) {
    var layer = container.layers[i];
    var path = prefix ? prefix + "/" + layer.name : layer.name;
    var b = "";
    try {
      var bounds = layer.bounds;
      b = [
        unitValue(bounds[0]),
        unitValue(bounds[1]),
        unitValue(bounds[2]),
        unitValue(bounds[3])
      ].join(",");
    } catch (e1) {}

    var text = "";
    if (layer.typename === "ArtLayer") {
      try {
        if (layer.kind === LayerKind.TEXT) {
          text = layer.textItem.contents;
        }
      } catch (e2) {}
    }

    lines.push([depth, cleanText(path), cleanText(layer.typename), layer.visible, b, cleanText(text)].join("\t"));

    if (layer.typename === "LayerSet") {
      walk(layer, path, depth + 1);
    }
  }
}

walk(doc, "", 0);

var f = new File(outPath);
f.encoding = "UTF-8";
f.open("w");
f.write(lines.join("\n"));
f.close();

doc.close(SaveOptions.DONOTSAVECHANGES);
"wrote " + outPath;
