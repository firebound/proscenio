import React from "react";

import type { DocSnapshot } from "../../hooks/useDocSnapshot";
import { Accordion } from "../common/Accordion";
import { KeyValueRow } from "../common/KeyValueRow";

interface Props {
    doc: DocSnapshot | null;
    onRefresh: () => void;
}

export const DocSection: React.FC<Props> = ({ doc, onRefresh }) => (
    <Accordion title="Active document" hint="Doc name + canvas dimensions">
        {doc === null ? (
            <sp-body size="XS" className="muted">No document open in Photoshop.</sp-body>
        ) : (
            <>
                <KeyValueRow label="name" value={doc.name} mono />
                <KeyValueRow label="canvas" value={`${doc.width} x ${doc.height} px`} mono />
            </>
        )}
        <sp-action-button onClick={onRefresh}>Refresh</sp-action-button>
    </Accordion>
);
