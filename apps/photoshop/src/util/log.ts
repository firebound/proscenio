// Tiny logger for the UXP panels. UXP's DevTools console is the only
// runtime debugger we have, so the goal here is just to gate noise by
// level + tag a single prefix on every line so logs from different
// hooks remain greppable.
//
// Levels (most to least verbose): trace > debug > info > warn > error > off.
// Default level is `info`; flip at runtime via DevTools:
//
//     window.proscenio.setLogLevel("debug")
//
// The choice persists in `localStorage` so reloading the plugin keeps
// the level. Reading happens lazily on every call so a flip from the
// console takes effect immediately - no panel reload needed.

export type LogLevel = "trace" | "debug" | "info" | "warn" | "error" | "off";

const ORDER: Record<LogLevel, number> = {
    trace: 10,
    debug: 20,
    info: 30,
    warn: 40,
    error: 50,
    off: 100,
};

const STORAGE_KEY = "proscenio.logLevel";
const DEFAULT_LEVEL: LogLevel = "info";
const CACHE_MS = 500;

let currentLevel: LogLevel = DEFAULT_LEVEL;
let cacheUntil = 0;

function loadLevel(): LogLevel {
    try {
        const raw = window.localStorage.getItem(STORAGE_KEY);
        if (raw !== null && raw in ORDER) return raw as LogLevel;
    } catch {
        // ignore
    }
    return DEFAULT_LEVEL;
}

function liveLevel(): LogLevel {
    const now = Date.now();
    if (now > cacheUntil) {
        currentLevel = loadLevel();
        cacheUntil = now + CACHE_MS;
    }
    return currentLevel;
}

function persistLevel(level: LogLevel): void {
    try {
        window.localStorage.setItem(STORAGE_KEY, level);
    } catch {
        // ignore
    }
}

export function setLogLevel(level: LogLevel): void {
    if (!(level in ORDER)) {
        console.warn(`[proscenio] unknown log level "${level}". Use one of:`, Object.keys(ORDER));
        return;
    }
    currentLevel = level;
    cacheUntil = Date.now() + CACHE_MS;
    persistLevel(level);
    console.info(`[proscenio] log level set to "${level}"`);
}

export function getLogLevel(): LogLevel {
    return liveLevel();
}

function enabled(level: LogLevel): boolean {
    return ORDER[level] >= ORDER[liveLevel()];
}

function format(tag: string, args: unknown[]): unknown[] {
    return [`[proscenio:${tag}]`, ...args];
}

export const log = {
    trace(tag: string, ...args: unknown[]): void {
        if (enabled("trace")) console.debug(...format(tag, args));
    },
    debug(tag: string, ...args: unknown[]): void {
        if (enabled("debug")) console.debug(...format(tag, args));
    },
    info(tag: string, ...args: unknown[]): void {
        if (enabled("info")) console.info(...format(tag, args));
    },
    warn(tag: string, ...args: unknown[]): void {
        if (enabled("warn")) console.warn(...format(tag, args));
    },
    error(tag: string, ...args: unknown[]): void {
        if (enabled("error")) console.error(...format(tag, args));
    },
};

// Expose a runtime control surface on `window.proscenio` so the
// console can flip levels without a code edit. `window.proscenio` is
// reserved for this debug shim; do not import it from app code.
declare global {
    interface Window {
        proscenio?: {
            setLogLevel: (level: LogLevel) => void;
            getLogLevel: () => LogLevel;
            levels: LogLevel[];
        };
    }
}

if (typeof window !== "undefined") {
    window.proscenio = {
        setLogLevel,
        getLogLevel,
        levels: Object.keys(ORDER) as LogLevel[],
    };
}
