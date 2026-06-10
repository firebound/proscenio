// Photoshop-style collapsible section mirroring the host's Properties /
// Layers panel headers. Open state is local so toggling one accordion
// does not cascade re-renders into siblings.

import React from "react";

let idCounter = 0;
function nextId(): number {
    idCounter += 1;
    return idCounter;
}

interface Props {
    title: string;
    /** Optional small label rendered next to the title (e.g. counts).
     *  Accepts `undefined` so callers can pass derived state directly. */
    badge?: string | undefined;
    /** Closed by default for sections the artist rarely needs (Import). */
    defaultOpen?: boolean;
    /** Long-form description; shown as an HTML title tooltip on the
     *  header so we do not have to render a permanent hint line. */
    hint?: string;
    children: React.ReactNode;
}

export const Accordion: React.FC<Props> = ({
    title,
    badge,
    defaultOpen = true,
    hint,
    children,
}) => {
    const [open, setOpen] = React.useState(defaultOpen);
    const onToggle = React.useCallback(() => { setOpen((o) => !o); }, []);
    const onKey = React.useCallback((e: React.KeyboardEvent) => {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setOpen((o) => !o);
        }
    }, []);
    const bodyId = React.useMemo(() => `accordion-body-${nextId()}`, []);

    return (
        <section className={`accordion ${open ? "open" : "closed"}`}>
            { }
            <span
                className="accordion-header"
                role="button"
                tabIndex={0}
                title={hint}
                aria-expanded={open}
                aria-controls={bodyId}
                onClick={onToggle}
                onKeyDown={onKey}
            >
                <span className="accordion-chevron">{open ? "v" : ">"}</span>
                <span className="accordion-title">{title}</span>
                {badge !== undefined && <span className="accordion-badge">{badge}</span>}
            </span>
            {open && <div id={bodyId} className="accordion-body">{children}</div>}
        </section>
    );
};
