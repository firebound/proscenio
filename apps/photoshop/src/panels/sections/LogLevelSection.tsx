// Debug logging control. Sets the runtime log level the `log` util gates
// on, so an artist hitting a bug can flip to `trace` / `debug` from the
// panel (no DevTools console command needed) and read the output in the
// UXP Developer Tools console. The level persists in localStorage.

import React from "react";

import { Accordion } from "../../components/Accordion";
import { KeyValueRow } from "../../components/KeyValueRow";
import { getLogLevel, setLogLevel, LOG_LEVELS, type LogLevel } from "../../utils/log";

export const LogLevelSection: React.FC = () => {
    const [level, setLevel] = React.useState<LogLevel>(() => getLogLevel());

    const onChange = React.useCallback((e: React.SyntheticEvent) => {
        const next = (e.target as HTMLSelectElement).value as LogLevel;
        setLogLevel(next);
        setLevel(next);
    }, []);

    return (
        <Accordion
            title="Debug logging"
            hint="Sets how much Proscenio logs to the UXP Developer Tools console. Use trace / debug when reproducing a bug; the choice persists across reloads."
            defaultOpen={false}
        >
            <KeyValueRow label="level">
                <select className="tag-select" value={level} onChange={onChange}>
                    {LOG_LEVELS.map((l) => (
                        <option key={l} value={l}>{l}</option>
                    ))}
                </select>
            </KeyValueRow>
            <sp-body size="XS" className="muted">
                Logs are tagged [proscenio:&lt;area&gt;]. Read them in Plugins &gt; Development &gt; Developer Tools.
            </sp-body>
        </Accordion>
    );
};
