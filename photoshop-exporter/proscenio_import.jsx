#target photoshop
// Proscenio -- Photoshop importer
// Reads a SPEC 006 v1 PSD manifest (matches schemas/psd_manifest.schema.json)
// and stamps every layer into a fresh PSD document at its declared
// `position` and `size`. Used to bootstrap test PSDs from existing
// Blender fixtures (e.g. examples/doll/) without authoring by hand.
//
// Run: File > Scripts > Browse... -> proscenio_import.jsx -> pick manifest.json.
//
// Conventions:
// - kind=polygon -> single layer, name = manifest layer name.
// - kind=sprite_frame -> LayerSet with the manifest layer name; child
//   layers named by frame index (matches the Wave 6.1 exporter D9
//   primary mechanism).
// - Layers stamped in z_order DESCENDING (so the lowest z_order ends up
//   on top in the Photoshop layer stack -- matches the export-side
//   convention where z_order 0 is the front layer).
// - Hidden layers in the source manifest are still emitted but left
//   visible (manifest does not carry visibility metadata).
//
// Compatible with Photoshop CC 2015 and later -- uses `var`, string
// concatenation, no arrow functions or template literals.
//
// SPDX-License-Identifier: GPL-3.0-or-later

(function () {
    var manifestFile = File.openDialog(
        "Select a Proscenio PSD manifest (.json)",
        "JSON files:*.json,All:*.*"
    );
    if (manifestFile === null) return;
    if (!manifestFile.exists) {
        alert("Manifest not found: " + manifestFile.fsName);
        return;
    }

    manifestFile.encoding = "UTF-8";
    if (!manifestFile.open("r")) {
        alert("Could not open " + manifestFile.fsName);
        return;
    }
    var raw = manifestFile.read();
    manifestFile.close();

    var manifest;
    try {
        manifest = parseJsonText(raw);
    } catch (parseErr) {
        alert("Manifest is not valid JSON: " + parseErr);
        return;
    }

    if (!manifest || manifest.format_version !== 1) {
        alert(
            "Unsupported manifest format_version " +
            (manifest ? manifest.format_version : "<missing>") +
            "; this importer expects 1."
        );
        return;
    }
    if (!isArray(manifest.layers)) {
        alert("Manifest is missing the `layers` array.");
        return;
    }

    var manifestDir = manifestFile.parent;
    var docName = manifest.doc || "imported.psd";
    var docWidth = manifest.size && manifest.size[0] ? manifest.size[0] : 1024;
    var docHeight = manifest.size && manifest.size[1] ? manifest.size[1] : 1024;

    var savedRulerUnits = app.preferences.rulerUnits;
    var savedTypeUnits = app.preferences.typeUnits;
    app.preferences.rulerUnits = Units.PIXELS;
    app.preferences.typeUnits = TypeUnits.PIXELS;

    var stamped = 0;
    try {
        var doc = app.documents.add(
            new UnitValue(docWidth, "px"),
            new UnitValue(docHeight, "px"),
            72,
            docName,
            NewDocumentMode.RGB,
            DocumentFill.TRANSPARENT
        );

        // Photoshop layer stack: first added = bottom. Manifest z_order 0 =
        // front, so iterate descending -> highest z_order added first
        // (bottom of stack), z_order 0 added last (top of stack).
        var layers = manifest.layers.slice();
        layers.sort(function (a, b) { return b.z_order - a.z_order; });

        for (var i = 0; i < layers.length; i++) {
            var entry = layers[i];
            if (entry.kind === "polygon") {
                if (stampPolygon(doc, entry, manifestDir)) stamped += 1;
            } else if (entry.kind === "sprite_frame") {
                if (stampSpriteFrame(doc, entry, manifestDir)) stamped += 1;
            } else {
                // Unknown kind -- skip rather than abort, so a partial import
                // still surfaces every layer the importer does understand.
            }
        }

        var savePath = new File(manifestDir + "/" + docName);
        var psdOpts = new PhotoshopSaveOptions();
        psdOpts.alphaChannels = true;
        psdOpts.embedColorProfile = true;
        psdOpts.layers = true;
        psdOpts.spotColors = false;
        // asCopy = false so the open doc is associated with the saved file
        // (otherwise subsequent calls to doc.path throw "document not saved").
        doc.saveAs(savePath, psdOpts, false, Extension.LOWERCASE);

        alert(
            "Proscenio import complete:\n" +
            stamped + " entry(ies) stamped -> " + savePath.fsName
        );
    } finally {
        // Restore PS preferences regardless of outcome -- otherwise an
        // exception leaves rulerUnits / typeUnits stuck on PIXELS until
        // the user manually resets them or restarts Photoshop.
        app.preferences.rulerUnits = savedRulerUnits;
        app.preferences.typeUnits = savedTypeUnits;
    }

    /**
     * @param {Document} targetDoc
     * @param {object} entry
     * @param {Folder} baseDir
     * @returns {boolean}
     */
    function stampPolygon(targetDoc, entry, baseDir) {
        var pngFile = resolvePath(baseDir, entry.path);
        if (pngFile === null || !pngFile.exists) {
            $.writeln("[proscenio_import] missing PNG: " + (entry.path || "<no path>"));
            return false;
        }
        if (!hasPositionAndSize(entry)) {
            $.writeln("[proscenio_import] polygon " + entry.name + " missing position/size; skipped");
            return false;
        }
        var placed = placeAndPosition(
            targetDoc,
            pngFile,
            entry.position[0],
            entry.position[1],
            entry.size[0],
            entry.size[1]
        );
        if (placed === null) return false;
        placed.name = entry.name;
        return true;
    }

    /**
     * @param {Document} targetDoc
     * @param {object} entry
     * @param {Folder} baseDir
     * @returns {boolean}
     */
    function stampSpriteFrame(targetDoc, entry, baseDir) {
        if (!isArray(entry.frames) || entry.frames.length < 2) {
            $.writeln("[proscenio_import] sprite_frame " + entry.name + " has < 2 frames; skipped");
            return false;
        }
        if (!hasPositionAndSize(entry)) {
            $.writeln(
                "[proscenio_import] sprite_frame " + entry.name +
                " missing position/size; skipped"
            );
            return false;
        }
        var group = targetDoc.layerSets.add();
        group.name = entry.name;
        var stampedFrames = 0;
        for (var i = 0; i < entry.frames.length; i++) {
            var frame = entry.frames[i];
            var pngFile = resolvePath(baseDir, frame.path);
            if (pngFile === null || !pngFile.exists) {
                $.writeln("[proscenio_import]   missing frame PNG: " + frame.path);
                continue;
            }
            var placed = placeAndPosition(
                targetDoc,
                pngFile,
                entry.position[0],
                entry.position[1],
                entry.size[0],
                entry.size[1]
            );
            if (placed === null) continue;
            placed.name = String(frame.index);
            placed.move(group, ElementPlacement.PLACEATEND);
            stampedFrames += 1;
        }
        if (stampedFrames === 0) {
            group.remove();
            return false;
        }
        return true;
    }

    /**
     * Open a PNG, copy its single layer into ``targetDoc``, translate to
     * (x, y) so its top-left lands at the manifest position. Returns the
     * pasted layer in the target doc, or null on failure.
     *
     * @param {Document} targetDoc
     * @param {File} pngFile
     * @param {number} targetX  PSD pixels, top-left of the placed layer.
     * @param {number} targetY
     * @param {number} expectedW  Manifest-declared layer width (sanity).
     * @param {number} expectedH  Manifest-declared layer height (sanity).
     */
    function placeAndPosition(targetDoc, pngFile, targetX, targetY, expectedW, expectedH) {
        var srcDoc;
        try {
            srcDoc = app.open(pngFile);
        } catch (openErr) {
            $.writeln("[proscenio_import] could not open " + pngFile.fsName + ": " + openErr);
            return null;
        }
        var duped = null;
        var deltaX = 0;
        var deltaY = 0;
        try {
            // Source layer bounds before duplication.
            var srcLayer = srcDoc.activeLayer;
            var bounds = srcLayer.bounds;
            var srcLeft = bounds[0].as("px");
            var srcTop = bounds[1].as("px");
            var srcRight = bounds[2].as("px");
            var srcBottom = bounds[3].as("px");
            var srcW = srcRight - srcLeft;
            var srcH = srcBottom - srcTop;

            // Sanity warning when manifest size disagrees with PNG bounds --
            // this can happen when frames are padded by the importer
            // post-export (D10) or when the rendered PNG was trimmed.
            if (Math.abs(srcW - expectedW) > 1 || Math.abs(srcH - expectedH) > 1) {
                $.writeln(
                    "[proscenio_import] " + pngFile.name +
                    " bounds " + srcW + "x" + srcH +
                    " differ from manifest " + expectedW + "x" + expectedH +
                    " -- using PNG bounds for placement."
                );
            }

            duped = srcLayer.duplicate(targetDoc, ElementPlacement.PLACEATBEGINNING);
            // Photoshop layers translate by deltas, not absolute coords.
            // After duplicate the layer keeps its source bounds; offset to
            // land top-left at (targetX, targetY).
            deltaX = targetX - srcLeft;
            deltaY = targetY - srcTop;
        } finally {
            // Close srcDoc regardless of whether bounds / duplicate threw.
            // Without this, an exception leaves srcDoc orphaned in
            // Photoshop's open-document list -- catastrophic on a 22-layer
            // batch import where every leak compounds.
            srcDoc.close(SaveOptions.DONOTSAVECHANGES);
        }
        if (duped === null) return null;
        duped.translate(new UnitValue(deltaX, "px"), new UnitValue(deltaY, "px"));
        return duped;
    }

    /**
     * @param {Folder} baseDir
     * @param {string} relative
     * @returns {File|null}
     */
    function resolvePath(baseDir, relative) {
        if (typeof relative !== "string" || relative === "") return null;
        return new File(baseDir + "/" + relative);
    }

    function isArray(value) {
        return Object.prototype.toString.call(value) === "[object Array]";
    }

    /**
     * Defensive null guard for entry.position / entry.size before the
     * placeAndPosition call dereferences index 0 / 1 on each. The schema
     * already requires both fields, but JSX does not validate strictly,
     * so a malformed manifest must surface as a skip + log line rather
     * than an unhandled TypeError that aborts the whole import.
     * @param {object} entry
     * @returns {boolean}
     */
    function hasPositionAndSize(entry) {
        return (
            isArray(entry.position) && entry.position.length >= 2 &&
            isArray(entry.size) && entry.size.length >= 2
        );
    }

    /**
     * Parse JSON text. Uses native JSON.parse when available; falls back
     * to eval() since older ExtendScript builds do not ship the JSON
     * global. The manifest is trusted local data so eval is acceptable.
     * @param {string} text
     */
    function parseJsonText(text) {
        if (typeof JSON !== "undefined" && JSON.parse) {
            return JSON.parse(text);
        }
        // eslint-disable-next-line no-eval
        return eval("(" + text + ")");
    }
})();
