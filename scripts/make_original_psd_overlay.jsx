var originalPsdPath = "/Users/a123/Downloads/债市周观察/债市周观察/债市周报.psd";
var finalPngPath = "/Users/a123/Downloads/债市周观察/债市周观察/长图/20260521新版/金葵花债市周观察20260521_原版.png";
var outputPsdPath = "/Users/a123/Downloads/债市周观察/债市周观察/长图/20260521新版/金葵花债市周观察20260521_原版.psd";

app.displayDialogs = DialogModes.NO;
var oldUnits = app.preferences.rulerUnits;
app.preferences.rulerUnits = Units.PIXELS;

var baseDoc = app.open(new File(originalPsdPath));
var pngDoc = app.open(new File(finalPngPath));

pngDoc.selection.selectAll();
pngDoc.selection.copy();
pngDoc.close(SaveOptions.DONOTSAVECHANGES);

app.activeDocument = baseDoc;
baseDoc.paste();

var layer = baseDoc.activeLayer;
layer.name = "新版原版长图_最终可见层";

function px(unitValue) {
  return unitValue.as("px");
}

var bounds = layer.bounds;
layer.translate(3042 - px(bounds[0]), 0 - px(bounds[1]));
layer.move(baseDoc, ElementPlacement.PLACEATBEGINNING);

var saveOptions = new PhotoshopSaveOptions();
saveOptions.layers = true;
saveOptions.alphaChannels = true;
saveOptions.annotations = true;
saveOptions.embedColorProfile = true;
saveOptions.spotColors = true;

baseDoc.saveAs(new File(outputPsdPath), saveOptions, true, Extension.LOWERCASE);
baseDoc.close(SaveOptions.DONOTSAVECHANGES);

app.preferences.rulerUnits = oldUnits;
