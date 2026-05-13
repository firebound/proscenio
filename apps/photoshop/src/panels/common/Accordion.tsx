// Photoshop-style collapsible section. The host's Properties / Layers
// panels use a tiny uppercase header + chevron; we mirror that here so
// the Proscenio panels feel native. State is local so toggling one
// accordion does not cascade re-renders into siblings.

import React from "react";

interface Props {
    title: string;
    /** Optional small label rendered next to the title (e.g. counts). */
    badge?: string;
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
    const onToggle = React.useCallback(() => setOpen((o) => !o), []);
    const onKey = React.useCallback((e: React.KeyboardEvent) => {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setOpen((o) => !o);
        }
    }, []);

    return (
        <section className={`accordion ${open ? "open" : "closed"}`}>
            {/* eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions */}
            <span
                className="accordion-header"
                role="button"
                tabIndex={0}
                title={hint}
                onClick={onToggle}
                onKeyDown={onKey}
            >
                <span className="accordion-chevron">{open ? "v" : ">"}</span>
                <span className="accordion-title">{title}</span>
                {badge !== undefined && <span className="accordion-badge">{badge}</span>}
            </span>
            {open && <div className="accordion-body">{children}</div>}
        </section>
    );
};
