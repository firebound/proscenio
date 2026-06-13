// Exercises the real PPU store: persistence guard + the subscribe/notify
// that fixes F-14 (an imported PPU never reaching the live panel state).
// Only localStorage is the external boundary; the store logic is real.

import { afterEach, describe, expect, it, vi } from "vitest";

import {
    DEFAULT_PIXELS_PER_UNIT,
    loadPixelsPerUnit,
    persistPixelsPerUnit,
    subscribePixelsPerUnit,
} from "../src/api/pixels-per-unit-store";

afterEach(() => {
    try {
        globalThis.localStorage.clear();
    } catch {
        // ignore
    }
});

describe("persistPixelsPerUnit", () => {
    it("returns a valid value unchanged (the value callers mirror into state)", () => {
        // localStorage itself is external I/O (and a no-op in this env);
        // the contract under test is the normalised return that callers do
        // `setState(persistPixelsPerUnit(v))` with.
        expect(persistPixelsPerUnit(250)).toBe(250);
    });

    it("normalises a non-positive / non-finite value to the default", () => {
        expect(persistPixelsPerUnit(0)).toBe(DEFAULT_PIXELS_PER_UNIT);
        expect(persistPixelsPerUnit(-5)).toBe(DEFAULT_PIXELS_PER_UNIT);
        expect(persistPixelsPerUnit(Number.NaN)).toBe(DEFAULT_PIXELS_PER_UNIT);
    });

    it("loadPixelsPerUnit falls back to the default when nothing is stored", () => {
        expect(loadPixelsPerUnit()).toBe(DEFAULT_PIXELS_PER_UNIT);
    });
});

describe("subscribePixelsPerUnit (F-14: import seeds the live value)", () => {
    it("notifies subscribers with the normalised value on persist", () => {
        const seen: number[] = [];
        const unsubscribe = subscribePixelsPerUnit((v) => seen.push(v));
        // Simulates the import flow seeding the imported manifest PPU.
        persistPixelsPerUnit(150);
        unsubscribe();
        expect(seen).toEqual([150]);
    });

    it("delivers the normalised (not raw) value to subscribers", () => {
        const fn = vi.fn();
        const unsubscribe = subscribePixelsPerUnit(fn);
        persistPixelsPerUnit(-1);
        unsubscribe();
        expect(fn).toHaveBeenCalledWith(DEFAULT_PIXELS_PER_UNIT);
    });

    it("stops notifying after unsubscribe", () => {
        const fn = vi.fn();
        const unsubscribe = subscribePixelsPerUnit(fn);
        unsubscribe();
        persistPixelsPerUnit(200);
        expect(fn).not.toHaveBeenCalled();
    });

    it("broadcasts to every registered subscriber", () => {
        const seen1: number[] = [];
        const seen2: number[] = [];
        const unsubscribe1 = subscribePixelsPerUnit((v) => seen1.push(v));
        const unsubscribe2 = subscribePixelsPerUnit((v) => seen2.push(v));
        persistPixelsPerUnit(150);
        unsubscribe1();
        unsubscribe2();
        expect(seen1).toEqual([150]);
        expect(seen2).toEqual([150]);
    });

    it("keeps notifying the rest when one subscriber throws", () => {
        // A broken subscriber must not break the chain (state would drift
        // across components that depend on the PPU update).
        const after = vi.fn();
        const unsubscribeBad = subscribePixelsPerUnit(() => { throw new Error("boom"); });
        const unsubscribeGood = subscribePixelsPerUnit(after);
        expect(() => persistPixelsPerUnit(150)).not.toThrow();
        unsubscribeBad();
        unsubscribeGood();
        expect(after).toHaveBeenCalledWith(150);
    });
});
