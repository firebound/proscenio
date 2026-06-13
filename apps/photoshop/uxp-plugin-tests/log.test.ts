// Exercises the real log-level control the Debug panel toggle drives.
// localStorage is the only external boundary (a no-op here); the level
// state + gating is real logic.

import { afterEach, describe, expect, it } from "vitest";

import { getLogLevel, setLogLevel, LOG_LEVELS } from "../src/utils/log";

afterEach(() => {
    setLogLevel("info");
});

describe("log levels", () => {
    it("exposes the full ordered level list for UI pickers", () => {
        expect(LOG_LEVELS).toEqual(["trace", "debug", "info", "warn", "error", "off"]);
    });

    it("setLogLevel makes getLogLevel return the new level immediately", () => {
        setLogLevel("debug");
        expect(getLogLevel()).toBe("debug");
        setLogLevel("error");
        expect(getLogLevel()).toBe("error");
    });

    it("rejects an unknown level, leaving the current one intact", () => {
        setLogLevel("warn");
        setLogLevel("bogus" as never);
        expect(getLogLevel()).toBe("warn");
    });
});
