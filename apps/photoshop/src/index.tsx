// Plugin entrypoint. Registers the single Proscenio exporter panel
// (10.3+). Wave 10.5 adds an importer panel alongside; until then
// this is the only entrypoint the manifest exposes.

import React from "react";
import { entrypoints } from "uxp";

import "./styles.css";
import { PanelController } from "./controllers/PanelController";
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

entrypoints.setup({
    plugin: {
        create() {
            console.log("Proscenio panel created");
        },
        destroy() {
            console.log("Proscenio panel destroyed");
        },
    },
    panels: {
        proscenioExporter: exporterController,
    },
});
