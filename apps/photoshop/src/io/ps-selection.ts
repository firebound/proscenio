// Click-to-select helper for the Validate / Debug surfaces. UXP
// exposes layer selection through `action.batchPlay` rather than a
// direct Layer.select() method, so this module wraps the descriptor
// so the panel can stay focused on UI concerns.
//
// `layerPath` is the chain of layer names from the document root down
// to the leaf - the same shape `PngWrite.layerPath` carries. Names
// must match the live PSD (the planner uses display-name semantics on
// the manifest, but selection has to use the raw PS layer name).

import { action, core } from "photoshop";

export async function selectLayerByPath(layerPath: readonly string[]): Promise<void> {
    if (layerPath.length === 0) return;
    const leaf = layerPath[layerPath.length - 1];
    await core.executeAsModal(
        async () => {
            await action.batchPlay(
                [
                    {
                        _obj: "select",
                        _target: [{ _ref: "layer", _name: leaf }],
                        makeVisible: false,
                        _options: { dialogOptions: "dontDisplay" },
                    },
                ],
                {},
            );
        },
        { commandName: "Select Proscenio layer" },
    );
}
