import React from "react";
import type { UxpFolder } from "uxp";

import { Accordion } from "../common/Accordion";
import { KeyValueRow } from "../common/KeyValueRow";

interface Props {
    folder: UxpFolder | null;
    onPick: () => void;
    onClear: () => void;
}

export const FolderSection: React.FC<Props> = ({ folder, onPick, onClear }) => (
    <Accordion
        title="Output folder"
        hint="Where the export writes the manifest + PNGs. The path persists across plugin reloads."
    >
        {folder === null ? (
            <sp-body size="XS" className="muted">No folder picked.</sp-body>
        ) : (
            <KeyValueRow label="path" mono>
                <span title={folder.nativePath}>{folder.nativePath}</span>
            </KeyValueRow>
        )}
        <div className="row">
            <sp-action-button onClick={onPick}>
                {folder === null ? "Pick folder" : "Change folder"}
            </sp-action-button>
            {folder !== null && <sp-action-button onClick={onClear}>Forget</sp-action-button>}
        </div>
    </Accordion>
);
