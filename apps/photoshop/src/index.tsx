// Plugin entrypoint. Registers the two Proscenio panels:
//
// - `proscenioExporter`: doc info + folder + export options + import.
// - `proscenioDebug`: standalone dry-run preview window with the
//   manifest entries + skipped layers list.

import React from "react";
import { entrypoints } from "uxp";

import "./styles.css";
import { PanelController } from "./controllers/PanelController";
import { ProscenioDebugPanel } from "./panels/ProscenioDebugPanel";
import { ProscenioExporter } from "./panels/ProscenioExporter";

const exporterController = new PanelController(() => <ProscenioExporter />, {
    id: "proscenioExporter",
    menuItems: [
        {
            id: "reload",
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
            id: "reload",
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
            console.log("Proscenio plugin created");
        },
        destroy() {
            console.log("Proscenio plugin destroyed");
        },
    },
    panels: {
        proscenioExporter: exporterController,
        proscenioDebug: debugController,
    },
});
