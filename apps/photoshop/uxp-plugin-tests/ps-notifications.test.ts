// Unit tests for the PS notification subscription wrapper. Drives the
// host mock's action.addNotificationListener, exercising the three
// return shapes (void / handle / Promise<handle>) and the teardown +
// cancel-before-resolve paths.

import { afterEach, describe, expect, it, vi } from "vitest";

import { action } from "photoshop";

import { subscribeToEvents } from "../src/api/ps-notifications";

const events = [{ event: "imageChanged" }];

afterEach(() => {
    vi.restoreAllMocks();
});

function stubListener(impl: () => unknown): void {
    vi.spyOn(action, "addNotificationListener").mockImplementation(impl as never);
}

describe("subscribeToEvents", () => {
    it("removes a synchronous handle on teardown", () => {
        const remove = vi.fn();
        stubListener(() => ({ remove }));
        const teardown = subscribeToEvents(events, () => {});
        teardown();
        expect(remove).toHaveBeenCalledOnce();
    });

    it("adopts a promise-resolved handle and removes it on teardown", async () => {
        const remove = vi.fn();
        const handle = Promise.resolve({ remove });
        stubListener(() => handle);
        const teardown = subscribeToEvents(events, () => {});
        await handle;
        teardown();
        expect(remove).toHaveBeenCalledOnce();
    });

    it("removes a late handle when teardown ran before it resolved", async () => {
        const remove = vi.fn();
        const handle = Promise.resolve({ remove });
        stubListener(() => handle);
        const teardown = subscribeToEvents(events, () => {});
        teardown(); // cancel before the promise resolves
        await handle;
        expect(remove).toHaveBeenCalledOnce();
    });

    it("tolerates a void return with no teardown handle", () => {
        stubListener(() => undefined);
        const teardown = subscribeToEvents(events, () => {});
        expect(() => teardown()).not.toThrow();
    });

    it("swallows a throwing subscribe", () => {
        stubListener(() => {
            throw new Error("addNotificationListener exploded");
        });
        expect(() => subscribeToEvents(events, () => {})).not.toThrow();
    });
});
