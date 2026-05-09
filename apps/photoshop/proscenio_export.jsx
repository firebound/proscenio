#target photoshop
// Proscenio -- Photoshop exporter
// Exports visible layers as PNG plus a position JSON manifest (v1) suitable
// for the Proscenio Blender importer (SPEC 006).
//
// Output layout (matches schemas/psd_manifest.schema.json):
//
//   The exporter creates an `export/` subfolder next to the PSD and
//   writes everything inside:
//       <docpath>/export/<doc>.photoshop_exported.json
//       <docpath>/export/images/<layer>.png
//       <docpath>/export/images/<sprite_frame>/<index>.png
//
//   Manifest path entries are relative to the manifest's own parent
//   ("images/<layer>.png", never "<doc>/images/...").
//
//   {
//     "format_version": 1,
//     "doc": "dummy.psd",
//     "size": [1024, 1024],
//     "pixels_per_unit": 100,
//     "layers": [
//       { "kind": "polygon", "name": "torso", "path": "...",
//         "position": [120, 340], "size": [180, 240], "z_order": 0 },
//       { "kind": "sprite_frame", "name": "eye",
//         "position": [350, 200], "size": [32, 32], "z_order": 1,
//         "frames": [
//           { "index": 0, "path": "..." },
//           { "index": 1, "path": "..." }
//         ] }
//     ]
//   }
//
// Conventions (SPEC 006 D9):
// - Hidden layers and `_`-prefixed layer names are skipped by default;
//   both are configurable per-run via the export dialog
//   (`skipHidden` / `skipUnderscorePrefix` options consumed by
//   `walkLayers`).
// - A LayerSet whose visible children are all non-LayerSet AND match a
//   uniform indexed frame convention emits as a single sprite_frame
//   entry (group name = mesh name, frames sorted by index). Sprite_frame
//   child filtering stays hardcoded regardless of dialog options.
// - Other LayerSets are walked recursively, output names join with `__`.
// - Top-level layers matching `<base>_<index>` flat naming are
//   aggregated post-walk into sprite_frame entries (fallback for users
//   who do not group their frames).
//
// Compatible with Photoshop CC 2015 and later -- uses `var`, string
// concatenation, no arrow functions or template literals.
//
// SPDX-License-Identifier: GPL-3.0-or-later

var MANIFEST_FORMAT_VERSION = 1;
var DEFAULT_PIXELS_PER_UNIT = 100;

(function () {
    if (!app.documents.length) {
        alert("Open a document first.");
        return;
    }

    var doc = app.activeDocument;
    if (doc.saved === false) {
        alert(
            "Save the document first.\n\n" +
            "The Proscenio exporter writes the manifest + layer PNGs " +
            "next to the .psd file, so the document must already be on " +
            "disk (File > Save) before running the export."
        );
        return;
    }
    var docPath = doc.path;
    var docName = doc.name.replace(/\.[^.]+$/, "");

    // Convention: write the export output into a sibling `export/` folder
    // next to the PSD. For the doll fixture this means
    // examples/doll/photoshop/export/. For ad-hoc PSDs it just creates
    // an export/ subfolder alongside.
    var outDir = new Folder(docPath + "/export");
    var imagesDir = new Folder(outDir + "/images");

    var options = showExportDialog(doc, outDir);
    if (options === null) return;  // user cancelled

    if (!outDir.exists) outDir.create();
    if (!imagesDir.exists) imagesDir.create();

    var savedRulerUnits = app.preferences.rulerUnits;
    app.preferences.rulerUnits = Units.PIXELS;

    var entries = [];
    var zCounter = { value: 0 };
    walkLayers(doc.layers, "", entries, zCounter, options);
    entries = aggregateFlatSpriteFrames(entries);

    var manifest = {
        format_version: MANIFEST_FORMAT_VERSION,
        doc: doc.name,
        size: [doc.width.as("px"), doc.height.as("px")],
        pixels_per_unit: DEFAULT_PIXELS_PER_UNIT,
        layers: entries
    };

    var manifestFile = new File(outDir + "/" + docName + ".photoshop_exported.json");
    manifestFile.encoding = "UTF-8";
    manifestFile.open("w");
    manifestFile.write(stringifyManifest(manifest));
    manifestFile.close();

    app.preferences.rulerUnits = savedRulerUnits;

    alert(
        "Proscenio export complete:\n" +
        entries.length + " entry(ies) -> " + outDir.fsName
    );
    if (options.openOutputFolder) {
        outDir.execute();
    }

    /**
     * Walk a layer collection, emitting polygon and sprite_frame entries.
     * @param {LayerSet["layers"]|Layers} layers
     * @param {string} prefix  Concatenated parent group names ("a__b__"); empty at top level.
     * @param {object[]} out   Mutable array of manifest entries.
     * @param {{value: number}} zCounter  Mutable z_order counter; incremented per emitted entry.
     */
    function walkLayers(layers, prefix, out, zCounter, opts) {
        for (var i = 0; i < layers.length; i++) {
            var layer = layers[i];
            if (opts.skipHidden && !layer.visible) continue;
            if (opts.skipUnderscorePrefix && layer.name.charAt(0) === "_") continue;

            if (layer.typename === "LayerSet") {
                if (qualifiesAsSpriteFrameGroup(layer)) {
                    var entry = exportSpriteFrameGroup(layer, prefix, zCounter.value);
                    if (entry !== null) {
                        out.push(entry);
                        zCounter.value += 1;
                    }
                    continue;
                }
                var nestedPrefix = prefix === "" ? layer.name : prefix + "__" + layer.name;
                walkLayers(layer.layers, nestedPrefix, out, zCounter, opts);
                continue;
            }

            var name = prefix === "" ? layer.name : prefix + "__" + layer.name;
            var poly = exportPolygonLayer(layer, name, zCounter.value);
            if (poly !== null) {
                out.push(poly);
                zCounter.value += 1;
            }
        }
    }

    /**
     * @param {LayerSet} group
     * @returns {boolean}
     */
    function qualifiesAsSpriteFrameGroup(group) {
        var children = group.layers;
        if (children.length < 2) return false;
        var visibleChildren = [];
        for (var i = 0; i < children.length; i++) {
            var child = children[i];
            if (!child.visible) continue;
            if (child.name.charAt(0) === "_") continue;
            if (child.typename === "LayerSet") return false;
            visibleChildren.push(child);
        }
        if (visibleChildren.length < 2) return false;

        var convention = null;
        var sharedBase = null;
        var indices = [];
        for (var j = 0; j < visibleChildren.length; j++) {
            var match = matchIndexedFrame(visibleChildren[j].name);
            if (match === null) return false;
            if (convention === null) {
                convention = match.convention;
                sharedBase = match.base;
            } else if (convention !== match.convention) {
                return false;
            } else if (sharedBase !== match.base) {
                return false;
            }
            indices.push(match.index);
        }
        return indicesAreContiguousFromZero(indices);
    }

    /**
     * @param {LayerSet} group
     * @param {string} prefix
     * @param {number} zOrder
     */
    function exportSpriteFrameGroup(group, prefix, zOrder) {
        var children = group.layers;
        var pairs = [];
        for (var i = 0; i < children.length; i++) {
            var child = children[i];
            if (!child.visible) continue;
            if (child.name.charAt(0) === "_") continue;
            var match = matchIndexedFrame(child.name);
            if (match === null) continue;
            pairs.push({ index: match.index, layer: child });
        }
        pairs.sort(function (a, b) { return a.index - b.index; });

        var meshName = prefix === "" ? group.name : prefix + "__" + group.name;
        var safeMeshName = sanitize(meshName);
        var groupDir = new Folder(imagesDir + "/" + safeMeshName);
        if (!groupDir.exists) groupDir.create();

        var maxBounds = null;
        var frameEntries = [];
        for (var k = 0; k < pairs.length; k++) {
            var pair = pairs[k];
            var pngFile = new File(groupDir + "/" + pair.index + ".png");
            var bounds = exportLayerToFile(pair.layer, pngFile);
            if (bounds === null) continue;
            if (
                maxBounds === null ||
                bounds.w * bounds.h > maxBounds.w * maxBounds.h
            ) {
                maxBounds = bounds;
            }
            frameEntries.push({
                index: pair.index,
                path: "images/" + safeMeshName + "/" + pair.index + ".png"
            });
        }
        if (maxBounds === null || frameEntries.length < 2) return null;
        return {
            kind: "sprite_frame",
            name: meshName,
            position: [Math.round(maxBounds.x), Math.round(maxBounds.y)],
            size: [Math.round(maxBounds.w), Math.round(maxBounds.h)],
            z_order: zOrder,
            frames: frameEntries
        };
    }

    /**
     * @param {ArtLayer} layer
     * @param {string} name
     * @param {number} zOrder
     */
    function exportPolygonLayer(layer, name, zOrder) {
        var safeName = sanitize(name);
        var pngFile = new File(imagesDir + "/" + safeName + ".png");
        var bounds = exportLayerToFile(layer, pngFile);
        if (bounds === null) return null;
        return {
            kind: "polygon",
            name: name,
            path: "images/" + safeName + ".png",
            position: [Math.round(bounds.x), Math.round(bounds.y)],
            size: [Math.round(bounds.w), Math.round(bounds.h)],
            z_order: zOrder
        };
    }

    /**
     * Duplicate the layer into a temp doc, trim, save PNG, return bounds.
     * @param {ArtLayer} layer
     * @param {File} pngFile
     */
    function exportLayerToFile(layer, pngFile) {
        var bounds = layer.bounds;
        var x = bounds[0].as("px");
        var y = bounds[1].as("px");
        var w = bounds[2].as("px") - x;
        var h = bounds[3].as("px") - y;
        if (w <= 0 || h <= 0) return null;

        var workDoc = app.documents.add(
            doc.width, doc.height, doc.resolution,
            "proscenio_export_tmp", NewDocumentMode.RGB,
            DocumentFill.TRANSPARENT
        );
        app.activeDocument = doc;
        layer.duplicate(workDoc, ElementPlacement.PLACEATBEGINNING);
        app.activeDocument = workDoc;
        workDoc.trim(TrimType.TRANSPARENT);

        var pngOpts = new PNGSaveOptions();
        pngOpts.interlaced = false;
        pngOpts.compression = 9;
        workDoc.saveAs(pngFile, pngOpts, true, Extension.LOWERCASE);
        workDoc.close(SaveOptions.DONOTSAVECHANGES);
        app.activeDocument = doc;

        return { x: x, y: y, w: w, h: h };
    }

    /**
     * Mirrors blender-addon/core/psd_naming.py:match_indexed_frame.
     * @param {string} name
     */
    function matchIndexedFrame(name) {
        var pure = /^(\d+)$/.exec(name);
        if (pure !== null) return { convention: "digit", base: "", index: parseInt(pure[1], 10) };
        var framed = /^frame[_-](\d+)$/i.exec(name);
        if (framed !== null) return { convention: "frame_prefix", base: "", index: parseInt(framed[1], 10) };
        var grouped = /^([A-Za-z][A-Za-z0-9]*)[_-](\d+)$/.exec(name);
        if (grouped !== null) return { convention: "group_prefix", base: grouped[1], index: parseInt(grouped[2], 10) };
        return null;
    }

    /**
     * @param {number[]} indices
     */
    function indicesAreContiguousFromZero(indices) {
        var sorted = indices.slice().sort(function (a, b) { return a - b; });
        if (sorted[0] !== 0) return false;
        for (var i = 0; i < sorted.length; i++) {
            if (sorted[i] !== i) return false;
        }
        return true;
    }

    /**
     * Post-walk pass: aggregate top-level polygon entries that match the
     * flat <base>_<index> convention into sprite_frame entries (SPEC 006
     * D9 fallback).
     * @param {object[]} input
     */
    function aggregateFlatSpriteFrames(input) {
        var bucket = {};
        var leftover = [];
        for (var i = 0; i < input.length; i++) {
            var entry = input[i];
            if (entry.kind !== "polygon") {
                leftover.push(entry);
                continue;
            }
            var match = /^([A-Za-z][A-Za-z0-9]*)[_-](\d+)$/.exec(entry.name);
            if (match === null) {
                leftover.push(entry);
                continue;
            }
            var base = match[1];
            var idx = parseInt(match[2], 10);
            if (!bucket.hasOwnProperty(base)) bucket[base] = [];
            bucket[base].push({ index: idx, entry: entry });
        }
        for (var base in bucket) {
            if (!bucket.hasOwnProperty(base)) continue;
            var pairs = bucket[base];
            if (pairs.length < 2) {
                for (var k = 0; k < pairs.length; k++) leftover.push(pairs[k].entry);
                continue;
            }
            pairs.sort(function (a, b) { return a.index - b.index; });
            var indices = [];
            for (var p = 0; p < pairs.length; p++) indices.push(pairs[p].index);
            if (!indicesAreContiguousFromZero(indices)) {
                for (var m = 0; m < pairs.length; m++) leftover.push(pairs[m].entry);
                continue;
            }
            var maxBounds = null;
            var frameEntries = [];
            var zOrder = pairs[0].entry.z_order;
            for (var n = 0; n < pairs.length; n++) {
                var item = pairs[n].entry;
                var w = item.size[0];
                var h = item.size[1];
                if (maxBounds === null || w * h > maxBounds.w * maxBounds.h) {
                    maxBounds = { x: item.position[0], y: item.position[1], w: w, h: h };
                }
                frameEntries.push({ index: pairs[n].index, path: item.path });
            }
            leftover.push({
                kind: "sprite_frame",
                name: base,
                position: [maxBounds.x, maxBounds.y],
                size: [maxBounds.w, maxBounds.h],
                z_order: zOrder,
                frames: frameEntries
            });
        }
        leftover.sort(function (a, b) { return a.z_order - b.z_order; });
        for (var z = 0; z < leftover.length; z++) leftover[z].z_order = z;
        return leftover;
    }

    /**
     * @param {string} s
     */
    function sanitize(s) {
        return String(s).replace(/[^A-Za-z0-9_\-]/g, "_");
    }

    /**
     * Show the pre-export options dialog. Returns the chosen options
     * object on OK, or null if the user cancelled.
     * @param {Document} doc
     * @param {Folder} outDir
     */
    function showExportDialog(doc, outDir) {
        var dlg = new Window("dialog", "Proscenio - Export Manifest");
        dlg.alignChildren = "fill";
        dlg.margins = 16;
        dlg.spacing = 10;

        var summary = dlg.add("panel", undefined, "Document");
        summary.alignChildren = "left";
        summary.margins = 12;
        summary.add("statictext", undefined, "PSD: " + doc.name);
        summary.add(
            "statictext",
            undefined,
            "Canvas: " + doc.width.as("px") + " x " + doc.height.as("px") + " px"
        );
        summary.add("statictext", undefined, "Output: " + outDir.fsName);

        var opts = dlg.add("panel", undefined, "Options");
        opts.alignChildren = "left";
        opts.margins = 12;
        var skipHidden = opts.add("checkbox", undefined, "Skip hidden layers");
        skipHidden.value = true;
        var skipUnderscore = opts.add("checkbox", undefined, "Skip layers starting with `_`");
        skipUnderscore.value = true;
        var openAfter = opts.add("checkbox", undefined, "Open output folder when done");
        openAfter.value = false;

        var buttons = dlg.add("group");
        buttons.alignment = "right";
        var ok = buttons.add("button", undefined, "Export", { name: "ok" });
        var cancel = buttons.add("button", undefined, "Cancel", { name: "cancel" });

        var result = null;
        ok.onClick = function () {
            result = {
                skipHidden: skipHidden.value,
                skipUnderscorePrefix: skipUnderscore.value,
                openOutputFolder: openAfter.value
            };
            dlg.close();
        };
        cancel.onClick = function () { dlg.close(); };

        dlg.show();
        return result;
    }

    function stringifyManifest(m) {
        if (typeof JSON !== "undefined" && JSON.stringify) {
            return JSON.stringify(m, null, 2);
        }
        // Older ExtendScript builds do not ship the JSON global. Manual
        // serializer covers the manifest's bounded shape (objects,
        // arrays, strings, finite numbers, booleans, null).
        return manualStringify(m, "");
    }

    function manualStringify(value, indent) {
        if (value === null) return "null";
        var t = typeof value;
        if (t === "boolean") return value ? "true" : "false";
        if (t === "number") return isFinite(value) ? String(value) : "null";
        if (t === "string") return jsonQuote(value);
        if (Object.prototype.toString.call(value) === "[object Array]") {
            if (value.length === 0) return "[]";
            var nextIndent = indent + "  ";
            var arrParts = [];
            for (var i = 0; i < value.length; i++) {
                arrParts.push(nextIndent + manualStringify(value[i], nextIndent));
            }
            return "[\n" + arrParts.join(",\n") + "\n" + indent + "]";
        }
        if (t === "object") {
            var keys = [];
            for (var k in value) {
                if (Object.prototype.hasOwnProperty.call(value, k)) keys.push(k);
            }
            if (keys.length === 0) return "{}";
            var nextIndent2 = indent + "  ";
            var objParts = [];
            for (var j = 0; j < keys.length; j++) {
                var key = keys[j];
                objParts.push(
                    nextIndent2 + jsonQuote(key) + ": " +
                    manualStringify(value[key], nextIndent2)
                );
            }
            return "{\n" + objParts.join(",\n") + "\n" + indent + "}";
        }
        return "null";
    }

    function jsonQuote(s) {
        var out = "\"";
        for (var i = 0; i < s.length; i++) {
            var c = s.charAt(i);
            var code = s.charCodeAt(i);
            if (c === "\\" || c === "\"") out += "\\" + c;
            else if (c === "\n") out += "\\n";
            else if (c === "\r") out += "\\r";
            else if (c === "\t") out += "\\t";
            else if (c === "\b") out += "\\b";
            else if (c === "\f") out += "\\f";
            else if (code < 0x20) {
                var hex = code.toString(16);
                while (hex.length < 4) hex = "0" + hex;
                out += "\\u" + hex;
            }
            else out += c;
        }
        return out + "\"";
    }
})();
