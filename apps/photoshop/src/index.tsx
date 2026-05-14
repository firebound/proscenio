// Plugin entrypoint. Registers the four Proscenio panels:
//
// - `proscenioExporter`: doc info + folder + export options + import.
// - `proscenioDebug`: standalone dry-run preview window with the
//   manifest entries list.
// - `proscenioTags`: layer hierarchy + bracket-tag controls.
// - `proscenioValidate`: live warnings + skipped layers from the
//   dry-run preview.

import React from "react";
import { entrypoints } from "uxp";

import "./styles.css";
import { PanelController } from "./controllers/PanelController";
import { ProscenioDebugPanel } from "./panels/ProscenioDebugPanel";
import { ProscenioExporter } from "./panels/ProscenioExporter";
import { ProscenioTagsPanel } from "./panels/ProscenioTagsPanel";
import { ProscenioValidatePanel } from "./panels/ProscenioValidatePanel";
import { log } from "./util/log";

const exporterController = new PanelController(() => <ProscenioExporter />, {
    id: "proscenioExporter",
    menuItems: [
        {
            id: "exporter.reload",
            label: "Reload Plugin",
            enabled: true,
            checked: false,
            oninvoke: () => location.reload(),
        },
    ],
});

const debugController = new PanelController(() => <ProscenioDebugPanel />, {
    id: "proscenioDebug",
    menuItems: [
        {
            id: "debug.reload",
            label: "Reload Plugin",
            enabled: true,
            checked: false,
            oninvoke: () => location.reload(),
        },
    ],
});

const tagsController = new PanelController(() => <ProscenioTagsPanel />, {
    id: "proscenioTags",
    menuItems: [
        {
            id: "tags.reload",
            label: "Reload Plugin",
            enabled: true,
            checked: false,
            oninvoke: () => location.reload(),
        },
    ],
});

const validateController = new PanelController(() => <ProscenioValidatePanel />, {
    id: "proscenioValidate",
    menuItems: [
        {
            id: "validate.reload",
            label: "Reload Plugin",
            enabled: true,
            checked: false,
            oninvoke: () => location.reload(),
        },
    ],
});

entrypoints.setup({
    plugin: {
        create() {
            log.info("plugin", "created; window.proscenio.setLogLevel(...) to adjust verbosity");
        },
        destroy() {
            log.info("plugin", "destroyed");
        },
    },
    panels: {
        proscenioExporter: exporterController,
        proscenioDebug: debugController,
        proscenioTags: tagsController,
        proscenioValidate: validateController,
    },
});
