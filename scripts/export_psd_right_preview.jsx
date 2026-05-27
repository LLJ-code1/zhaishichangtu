var targetPsdPath = "/Users/a123/Downloads/债市周观察/债市周观察/weeks/2026-05-25_2026-05-29/outputs/20260521新版/金葵花债市周观察20260521_原版.psd";
var previewPath = "/private/tmp/债市周观察_checks/psd_right_preview_photoshop.png";

app.displayDialogs = DialogModes.NO;
var oldUnits = app.preferences.rulerUnits;
app.preferences.rulerUnits = Units.PIXELS;

var doc = app.open(new File(targetPsdPath));
var preview = doc.duplicate("psd_right_preview", true);
preview.crop([3042, 0, 4167, 7037]);

var pngOptions = new PNGSaveOptions();
preview.saveAs(new File(previewPath), pngOptions, true, Extension.LOWERCASE);
preview.close(SaveOptions.DONOTSAVECHANGES);
doc.close(SaveOptions.DONOTSAVECHANGES);

app.preferences.rulerUnits = oldUnits;
