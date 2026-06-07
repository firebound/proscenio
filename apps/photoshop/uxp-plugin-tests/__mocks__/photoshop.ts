// Vitest host mock for the UXP "photoshop" module, wired in through
// vitest.config.ts test.alias. The real module is a host global that
// only exists inside Photoshop, so api modules that import { app, core,
// action, constants } cannot load under plain vitest without it.
//
// Tests drive behavior by mutating `app.activeDocument` or configuring
// the vi.fn command stubs (core.executeAsModal / action.batchPlay).

import { vi } from "vitest";

// Mutable so a test can set the active document, then reset in afterEach.
// documents.add / open are vi.fn stubs the flow tests configure.
export const app = {
    activeDocument: null as unknown,
    documents: { add: vi.fn() },
    open: vi.fn(),
};

export const core = {
    // Default: run the callback inline so modal-wrapped code paths execute.
    executeAsModal: vi.fn(
        async (callback: (executionContext: unknown, descriptor: unknown) => unknown) =>
            callback({}, {}),
    ),
};

export const action = {
    batchPlay: vi.fn(async (): Promise<unknown[]> => []),
    addNotificationListener: vi.fn(),
};

export const constants = {
    DocumentFill: { TRANSPARENT: "transparent" },
    NewDocumentMode: { RGB: "rgb" },
    TrimType: { TRANSPARENT: "transparent" },
    ElementPlacement: { PLACEATEND: "placeAtEnd" },
};
