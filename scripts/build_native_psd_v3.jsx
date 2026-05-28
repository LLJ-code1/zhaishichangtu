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

    function findTextLayerByExact(doc, exactText) {
        var found = null;
        walk(doc, function (layer) {
            if (found !== null) {
                return;
            }
            if (layerText(layer) === exactText) {
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
        if (match.type === "exact") {
            return findTextLayerByExact(doc, match.text);
        }
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

    function setTextByMatch(doc, match, newText, label) {
        var layer = findTextLayerByMatch(doc, match);
        if (layer === null) {
            throw new Error("Cannot find text layer: " + label + " / " + match.text);
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

    function resizeLayerToBottom(layer, targetBottom) {
        var box = boundsOf(layer);
        var targetHeight = targetBottom - box.top;
        if (targetHeight <= 0 || box.height <= 0) {
            throw new Error("Invalid target height for layer: " + layer.name);
        }
        layer.resize(100, targetHeight / box.height * 100, AnchorPosition.TOPLEFT);
        moveLayerTo(layer, box.left, box.top);
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

    function styleTextLayerWithRanges(doc, layer, ranges) {
        app.activeDocument = doc;
        doc.activeLayer = layer;
        var textKey = currentTextKey();
        var existingRanges = textKey.getList(charIDToTypeID("Txtt"));
        var styleRanges = new ActionList();
        for (var i = 0; i < ranges.length; i++) {
            var range = ranges[i];
            var rangeDesc = new ActionDescriptor();
            rangeDesc.putInteger(charIDToTypeID("From"), range.from);
            rangeDesc.putInteger(charIDToTypeID("T   "), range.to);

            var styleDesc = existingRanges.getObjectValue(0).getObjectValue(charIDToTypeID("TxtS"));
            styleDesc.putObject(charIDToTypeID("Clr "), charIDToTypeID("RGBC"), rgbDescriptor(range.color));
            rangeDesc.putObject(charIDToTypeID("TxtS"), charIDToTypeID("TxtS"), styleDesc);
            styleRanges.putObject(charIDToTypeID("Txtt"), rangeDesc);
        }
        textKey.putList(charIDToTypeID("Txtt"), styleRanges);

        var setDesc = new ActionDescriptor();
        var ref = new ActionReference();
        ref.putEnumerated(charIDToTypeID("TxLr"), charIDToTypeID("Ordn"), charIDToTypeID("Trgt"));
        setDesc.putReference(charIDToTypeID("null"), ref);
        setDesc.putObject(charIDToTypeID("T   "), charIDToTypeID("TxLr"), textKey);
        executeAction(charIDToTypeID("setd"), setDesc, DialogModes.NO);
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

    function findArtLayerByNameAndVerticalRange(doc, name, topMin, topMax, x0) {
        var found = null;
        walk(doc, function (layer) {
            if (found !== null) {
                return;
            }
            if (layer.typename !== "ArtLayer" || layer.name !== name) {
                return;
            }
            var box = boundsOf(layer);
            if (box.right > x0 && box.top >= topMin && box.top <= topMax) {
                found = layer;
            }
        });
        return found;
    }

    function shouldShiftLayerBox(box, x0, shiftAfterY, shiftWhen, maxShiftLayerHeight, minShiftLayerTop) {
        if (box.right <= x0) {
            return false;
        }
        if (minShiftLayerTop && box.top < minShiftLayerTop) {
            return false;
        }
        if (maxShiftLayerHeight && box.height > maxShiftLayerHeight) {
            return false;
        }
        if (shiftWhen === "bottom_after_boundary") {
            return box.bottom > shiftAfterY;
        }
        return box.top >= shiftAfterY;
    }

    function layerKey(layer) {
        try {
            return String(layer.id);
        } catch (e) {}
        try {
            var box = boundsOf(layer);
            return layer.name + "|" + Math.round(box.left) + "|" + Math.round(box.top);
        } catch (ignored) {}
        return layer.name;
    }

    function markLayerProcessed(layer, processedLayerIds) {
        processedLayerIds[layerKey(layer)] = true;
    }

    function isLayerProcessed(layer, processedLayerIds) {
        return processedLayerIds[layerKey(layer)] === true;
    }

    function markLinkedLayerSet(layer, processedLayerIds) {
        markLayerProcessed(layer, processedLayerIds);
        try {
            for (var i = 0; i < layer.linkedLayers.length; i++) {
                markLayerProcessed(layer.linkedLayers[i], processedLayerIds);
            }
        } catch (e) {}
    }

    function shiftVisibleLayersBelow(container, x0, shiftAfterY, shiftY, shiftWhen, maxShiftLayerHeight, minShiftLayerTop, processedLayerIds) {
        processedLayerIds = processedLayerIds || {};
        for (var i = container.layers.length - 1; i >= 0; i--) {
            var layer = container.layers[i];
            if (!layer.visible) {
                continue;
            }

            var box = null;
            try {
                box = boundsOf(layer);
            } catch (e) {
                box = null;
            }

            if (box !== null && shouldShiftLayerBox(box, x0, shiftAfterY, shiftWhen, maxShiftLayerHeight, minShiftLayerTop)) {
                if (isLayerProcessed(layer, processedLayerIds)) {
                    continue;
                }
                markLinkedLayerSet(layer, processedLayerIds);
                layer.translate(0, shiftY);
                continue;
            }

            if (layer.typename === "LayerSet") {
                shiftVisibleLayersBelow(
                    layer,
                    x0,
                    shiftAfterY,
                    shiftY,
                    shiftWhen,
                    maxShiftLayerHeight,
                    minShiftLayerTop,
                    processedLayerIds
                );
            }
        }
    }

    function shiftLayersTopAtOrAfter(container, x0, boundaryY, shiftY, processedLayerIds) {
        if (Math.round(shiftY) === 0) {
            return;
        }
        processedLayerIds = processedLayerIds || {};
        for (var i = container.layers.length - 1; i >= 0; i--) {
            var layer = container.layers[i];
            if (!layer.visible) {
                continue;
            }

            var box = null;
            try {
                box = boundsOf(layer);
            } catch (e) {
                box = null;
            }

            if (box !== null && box.right > x0 && box.top >= boundaryY) {
                if (isLayerProcessed(layer, processedLayerIds)) {
                    continue;
                }
                markLinkedLayerSet(layer, processedLayerIds);
                layer.translate(0, shiftY);
                continue;
            }

            if (layer.typename === "LayerSet") {
                shiftLayersTopAtOrAfter(layer, x0, boundaryY, shiftY, processedLayerIds);
            }
        }
    }

    function matchesTargetedOffset(layer, box, x0, spec) {
        return layer.name === spec.layer_name &&
            box.right > x0 &&
            box.top >= spec.top_min &&
            box.top <= spec.top_max;
    }

    function applyTargetedOffsets(doc, x0, offsets) {
        if (!offsets) {
            return;
        }
        var moved = [];
        for (var i = 0; i < offsets.length; i++) {
            moved.push(false);
        }

        walk(doc, function (layer) {
            if (layer.typename !== "ArtLayer" || !layer.visible) {
                return;
            }
            var box = null;
            try {
                box = boundsOf(layer);
            } catch (e) {
                box = null;
            }
            if (box === null) {
                return;
            }
            for (var i = 0; i < offsets.length; i++) {
                if (moved[i]) {
                    continue;
                }
                var spec = offsets[i];
                if (matchesTargetedOffset(layer, box, x0, spec)) {
                    layer.translate(spec.dx || 0, spec.dy || 0);
                    moved[i] = true;
                    return;
                }
            }
        });

        for (var j = 0; j < offsets.length; j++) {
            if (!moved[j]) {
                throw new Error("Cannot find targeted offset layer: " + offsets[j].layer_name);
            }
        }
    }

    function maxContentBottom(section, nativeGroups, imageLayers) {
        var bottom = null;
        var i;
        if (section.content_keys) {
            for (i = 0; i < section.content_keys.length; i++) {
                var group = nativeGroups[section.content_keys[i]];
                if (!group) {
                    throw new Error("Missing dynamic content group: " + section.content_keys[i]);
                }
                var groupBottom = boundsOf(group).bottom;
                bottom = bottom === null ? groupBottom : Math.max(bottom, groupBottom);
            }
        }
        if (section.image_keys) {
            for (i = 0; i < section.image_keys.length; i++) {
                var imageLayer = imageLayers[section.image_keys[i]];
                if (!imageLayer) {
                    throw new Error("Missing dynamic image layer: " + section.image_keys[i]);
                }
                var imageBottom = boundsOf(imageLayer).bottom;
                bottom = bottom === null ? imageBottom : Math.max(bottom, imageBottom);
            }
        }
        if (bottom === null) {
            throw new Error("Dynamic section has no content anchor: " + section.name);
        }
        return bottom;
    }

    function resizeLayerFromSpec(doc, spec, x0, offsetY, targetBottom) {
        var layer = findArtLayerByNameAndVerticalRange(
            doc,
            spec.layer_name,
            spec.top_min + offsetY - 3,
            spec.top_max + offsetY + 3,
            x0
        );
        if (layer === null) {
            throw new Error("Cannot find dynamic gap layer: " + spec.layer_name + " / " + spec.top_min);
        }
        var oldBottom = boundsOf(layer).bottom;
        resizeLayerToBottom(layer, targetBottom);
        return { layer: layer, oldBottom: oldBottom };
    }

    function applyDynamicGaps(doc, data, nativeGroups, imageLayers, profile) {
        if (!profile || !profile.enabled) {
            return false;
        }

        var cumulativeShift = 0;
        for (var i = 0; i < profile.sections.length; i++) {
            var section = profile.sections[i];
            var contentBottom = maxContentBottom(section, nativeGroups, imageLayers);

            if (section.inner_layers) {
                for (var j = 0; j < section.inner_layers.length; j++) {
                    var inner = section.inner_layers[j];
                    resizeLayerFromSpec(doc, inner, data.x0, cumulativeShift, contentBottom + inner.bottom_gap);
                }
            }

            var resizedBackground = resizeLayerFromSpec(
                doc,
                section.background,
                data.x0,
                cumulativeShift,
                contentBottom + section.background.bottom_gap
            );
            var backgroundBox = boundsOf(resizedBackground.layer);
            var oldBoundary = resizedBackground.oldBottom;
            var sectionShift = backgroundBox.bottom - oldBoundary;
            shiftLayersTopAtOrAfter(doc, data.x0, oldBoundary, sectionShift);
            cumulativeShift += sectionShift;
        }

        var sourceLayer = findLayerByName(doc, "数据来源及风险提示_原生替换");
        if (sourceLayer !== null) {
            data.height = Math.round(boundsOf(sourceLayer).bottom + profile.footer_bottom_gap);
        }
        return true;
    }

    function cropDocumentHeight(doc, height) {
        if (!height) {
            return;
        }
        var currentHeight = px(doc.height);
        if (Math.round(currentHeight) === Math.round(height)) {
            return;
        }
        doc.crop([0, 0, px(doc.width), height]);
    }

    function applyLayoutAdjustments(doc, data, nativeGroups, imageLayers) {
        var adjustments = data.layout_adjustments;
        if (!adjustments) {
            return;
        }

        if (applyDynamicGaps(doc, data, nativeGroups, imageLayers, adjustments.dynamic_gaps)) {
            cropDocumentHeight(doc, data.height);
            return;
        }

        if (adjustments.hero_background) {
            var hero = adjustments.hero_background;
            var heroBackground = findArtLayerByNameAndVerticalRange(
                doc,
                hero.layer_name,
                hero.top_min,
                hero.top_max,
                data.x0
            );
            if (heroBackground === null) {
                throw new Error("Cannot find hero background layer: " + hero.layer_name);
            }
            resizeLayerToBottom(heroBackground, hero.target_bottom);
        }

        if (adjustments.shift_y && adjustments.shift_after_y) {
            shiftVisibleLayersBelow(
                doc,
                data.x0,
                adjustments.shift_after_y,
                adjustments.shift_y,
                adjustments.shift_when,
                adjustments.max_shift_layer_height,
                adjustments.min_shift_layer_top
            );
        }

        applyTargetedOffsets(doc, data.x0, adjustments.targeted_offsets);

        cropDocumentHeight(doc, data.height);
    }

    function renderNativeTextBlock(doc, blockKey, block) {
        var target = findTextLayerByMatch(doc, block.match);
        if (target === null) {
            throw new Error("Cannot find text target for block: " + blockKey + " / " + block.match.text);
        }
        var box = boundsOf(target);
        target.visible = false;

        app.activeDocument = doc;
        var layer = doc.artLayers.add();
        layer.kind = LayerKind.TEXT;
        layer.name = "native_v3_rich_text_" + blockKey;
        try {
            layer.move(target, ElementPlacement.PLACEBEFORE);
        } catch (e) {}

        var textItem = layer.textItem;
        textItem.kind = TextType.PARAGRAPHTEXT;
        textItem.contents = block.text;
        textItem.size = block.size;
        textItem.leading = block.leading;
        textItem.color = makeColor([24, 22, 20]);
        trySetFont(textItem, block.font);
        textItem.position = [box.left, box.top];
        textItem.width = UnitValue(block.box.width, "px");
        textItem.height = UnitValue(Math.max(block.box.height, block.estimated_height + 80), "px");
        try {
            textItem.justification = Justification.LEFT;
        } catch (ignored) {}

        styleTextLayerWithRanges(doc, layer, block.style_ranges);
        return layer;
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
        var layerMap = data.layer_map;
        var doc = app.open(new File(data.original_psd));

        setTextByMatch(doc, layerMap.text_layers.date.match, data.date, "日期_2026-5-21");
        setTextByMatch(doc, layerMap.text_layers.top_title.match, data.top_title, "首屏标题_国债收益率整体下行");
        setTextByMatch(doc, layerMap.text_layers.source_risk.match, data.source_risk, "数据来源及风险提示_原生替换");

        var nativeGroups = {};
        nativeGroups.top_intro = renderNativeTextBlock(doc, "top_intro", data.native_text_blocks.top_intro);
        nativeGroups.market_sentence = renderNativeTextBlock(doc, "market_sentence", data.native_text_blocks.market_sentence);
        nativeGroups.funding = renderNativeTextBlock(doc, "funding", data.native_text_blocks.funding);
        nativeGroups.fund_chart_title = renderNativeTextBlock(doc, "fund_chart_title", data.native_text_blocks.fund_chart_title);
        nativeGroups.risk_preference = renderNativeTextBlock(doc, "risk_preference", data.native_text_blocks.risk_preference);
        nativeGroups.outlook = renderNativeTextBlock(doc, "outlook", data.native_text_blocks.outlook);
        nativeGroups.strategy = renderNativeTextBlock(doc, "strategy", data.native_text_blocks.strategy);

        var imageLayers = {};
        imageLayers.table = placeImageIntoBounds(doc, data.assets.table, layerMap.image_layers.table.target_layer_name, "表1_20260521_原生替换");
        imageLayers.yield_chart = placeImageIntoBounds(doc, data.assets.yield_chart, layerMap.image_layers.yield_chart.target_layer_name, "图片1_国债收益率曲线_透明v3");
        imageLayers.fund_chart = placeImageIntoBounds(doc, data.assets.fund_chart, layerMap.image_layers.fund_chart.target_layer_name, "图片2_资金利率曲线_透明v3");

        applyLayoutAdjustments(doc, data, nativeGroups, imageLayers);

        savePsd(doc, data.output_psd);
        exportPreview(doc, data);
        doc.close(SaveOptions.DONOTSAVECHANGES);
    } finally {
        app.preferences.rulerUnits = oldUnits;
    }
})();
