// @ts-check
// Proscenio -- Photoshop exporter
// Exports visible layers as PNG plus a position JSON manifest (v1) suitable
// for the Proscenio Blender importer (SPEC 006).
//
// Output shape (matches schemas/psd_manifest.schema.json):
//
//   <doc>.json
//   <doc>/images/<layer>.png
//   <doc>/images/<sprite_frame>/<index>.png
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
// - Hidden layers skipped, layer names prefixed `_` skipped.
// - A LayerSet whose visible children are all non-LayerSet AND match a
//   uniform indexed frame convention emits as a single sprite_frame
//   entry (group name = mesh name, frames sorted by index).
// - Other LayerSets are walked recursively, output names join with `__`.
// - Top-level layers matching `<base>_<index>` flat naming are
//   aggregated post-walk into sprite_frame entries (fallback for users
//   who do not group their frames).
//
// Compatible with Photoshop CC 2015 and later -- uses `var`, string
// concatenation, no arrow functions or template literals.
//
// SPDX-License-Identifier: GPL-3.0-or-later

#target photoshop

var MANIFEST_FORMAT_VERSION = 1;
var DEFAULT_PIXELS_PER_UNIT = 100;

(function () {
    if (!app.documents.length) {
        alert("Open a document first.");
        return;
    }

    var doc = app.activeDocument;
    var docPath = doc.path;
    var docName = doc.name.replace(/\.[^.]+$/, "");
    var outDir = new Folder(docPath + "/" + docName);
    var imagesDir = new Folder(outDir + "/images");
    if (!outDir.exists) outDir.create();
    if (!imagesDir.exists) imagesDir.create();

    var savedRulerUnits = app.preferences.rulerUnits;
    app.preferences.rulerUnits = Units.PIXELS;

    var entries = [];
    var zCounter = { value: 0 };
    walkLayers(doc.layers, "", entries, zCounter);
    entries = aggregateFlatSpriteFrames(entries);

    var manifest = {
        format_version: MANIFEST_FORMAT_VERSION,
        doc: doc.name,
        size: [doc.width.as("px"), doc.height.as("px")],
        pixels_per_unit: DEFAULT_PIXELS_PER_UNIT,
        layers: entries
    };

    var manifestFile = new File(outDir + "/" + docName + ".json");
    manifestFile.encoding = "UTF-8";
    manifestFile.open("w");
    manifestFile.write(stringifyManifest(manifest));
    manifestFile.close();

    app.preferences.rulerUnits = savedRulerUnits;

    alert(
        "Proscenio export complete:\n" +
        entries.length + " entry(ies) -> " + outDir.fsName
    );

    /**
     * Walk a layer collection, emitting polygon and sprite_frame entries.
     * @param {LayerSet["layers"]|Layers} layers
     * @param {string} prefix  Concatenated parent group names ("a__b__"); empty at top level.
     * @param {object[]} out   Mutable array of manifest entries.
     * @param {{value: number}} zCounter  Mutable z_order counter; incremented per emitted entry.
     */
    function walkLayers(layers, prefix, out, zCounter) {
        for (var i = 0; i < layers.length; i++) {
            var layer = layers[i];
            if (!layer.visible) continue;
            if (layer.name.charAt(0) === "_") continue;

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
                walkLayers(layer.layers, nestedPrefix, out, zCounter);
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
                path: docName + "/images/" + safeMeshName + "/" + pair.index + ".png"
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
            path: docName + "/images/" + safeName + ".png",
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

    function stringifyManifest(m) {
        if (typeof JSON !== "undefined" && JSON.stringify) {
            return JSON.stringify(m, null, 2);
        }
        // Photoshop CC 2015+ ships JSON; older versions would need a polyfill.
        // Bail loudly rather than emit a half-broken manual encoding.
        throw new Error(
            "JSON.stringify unavailable; Photoshop CC 2015 or later required."
        );
    }
})();
