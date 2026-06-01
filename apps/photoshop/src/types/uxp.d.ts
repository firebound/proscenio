// Minimal ambient module shims for UXP / Photoshop runtime modules.
//
// Adobe does not publish `@types/uxp` or `@types/photoshop` on npm; the
// real type bundles ship with the UDT (UXP Developer Tool) install and
// are sourced from the local Photoshop UXP runtime at debug-load time.
// These shims keep `tsc --noEmit` honest until the real types land.
//
// Tighten member-by-member as the implementation grows - each panel /
// controller / IO helper should narrow what it consumes.

declare module "uxp" {
    export const entrypoints: {
        setup(config: {
            plugin?: {
                create?: (plugin: unknown) => void;
                destroy?: () => void;
            };
            panels?: Record<string, unknown>;
            commands?: Record<string, unknown>;
        }): void;
    };

    export const storage: {
        localFileSystem: LocalFileSystem;
        formats: { utf8: "utf8"; binary: "binary" };
    };

    /** XMP metadata bindings exposed by PS 25 / CC 2024 and later.
     *  Older Photoshop builds ship a UXP module without the `xmp`
     *  member; consumers should call `isXmpAvailable()` from
     *  `src/io/xmp.ts` rather than dereferencing the field directly. */
    export const xmp: XmpModule | undefined;

    export interface XmpModule {
        XMPMeta: XmpMetaCtor;
    }

    export interface XmpMetaCtor {
        new (raw?: string): XmpMetaInstance;
        registerNamespace?(uri: string, prefix: string): void;
    }

    export interface XmpMetaInstance {
        serialize(): string;
        setProperty(ns: string, key: string, value: string): void;
        getProperty(ns: string, key: string): { value?: string } | undefined;
        deleteProperty(ns: string, key: string): void;
        doesPropertyExist?(ns: string, key: string): boolean;
    }

    export interface LocalFileSystem {
        getFolder(): Promise<UxpFolder>;
        // Single-file picker. `types` accepts an array of accepted
        // extensions like `["json"]`; UXP filters the OS dialog.
        getFileForOpening(options?: { types?: string[]; allowMultiple?: false }): Promise<UxpFile | null>;
        // Resolves a filesystem path (or `file://` URL) to an entry.
        // Requires `localFileSystem: "fullAccess"` to read arbitrary
        // paths. The manifest reader uses it as a fallback when
        // `file.parent` is absent on the picked entry.
        getEntryWithUrl(url: string): Promise<UxpEntry>;
        createSessionToken(entry: UxpEntry): string;
        // Persistent tokens survive plugin reloads / Photoshop restarts.
        // Persist the returned string in localStorage; resolve back to
        // the folder via getEntryForPersistentToken on next session.
        createPersistentToken(entry: UxpEntry): Promise<string>;
        getEntryForPersistentToken(token: string): Promise<UxpEntry>;
    }

    export interface UxpEntry {
        readonly name: string;
        readonly nativePath: string;
        readonly isFile: boolean;
        readonly isFolder: boolean;
    }

    export interface UxpFolder extends UxpEntry {
        createFile(name: string, options?: { overwrite?: boolean }): Promise<UxpFile>;
        createFolder(name: string, options?: { overwrite?: boolean }): Promise<UxpFolder>;
        getEntry(name: string): Promise<UxpEntry>;
        getEntries(): Promise<UxpEntry[]>;
    }

    export interface UxpFile extends UxpEntry {
        write(contents: string | ArrayBuffer, options?: { format?: "utf8" | "binary"; append?: boolean }): Promise<void>;
        read(options?: { format?: "utf8" | "binary" }): Promise<string | ArrayBuffer>;
        /** Modern UXP exposes the parent folder of a picked entry
         *  directly. Older host builds (and a few PS regressions) drop
         *  this field; consumers must guard with `?.` and fall back to
         *  reconstructing the parent path from `nativePath`. */
        readonly parent?: UxpFolder;
    }
}

declare module "photoshop" {
    export const app: PhotoshopApp;
    export const core: PhotoshopCore;
    export const constants: PhotoshopConstants;
    export const action: {
        batchPlay(commands: unknown[], options?: unknown): Promise<unknown>;
        /** Subscribe to PS notification events. Return shape varies
         *  by UXP version: older builds return `void`, newer builds
         *  return a sync handle, recent builds return
         *  `Promise<handle>`. Consumers must probe at runtime. */
        addNotificationListener(
            events: readonly { event: string }[],
            callback: (event: { event: string }, descriptor: unknown) => void,
        ): Promise<PsNotificationListener> | PsNotificationListener | void;
    };

    export interface PsNotificationListener {
        remove(): void;
    }

    export interface PhotoshopApp {
        activeDocument: PsDocument | null;
        documents: PsDocumentCollection;
        // Opens a file (PNG, PSD, ...) as a new active document.
        open(file: unknown): Promise<PsDocument>;
    }

    export interface PsDocumentCollection extends ReadonlyArray<PsDocument> {
        add(opts: {
            width: number;
            height: number;
            resolution?: number;
            // Must be a `constants.NewDocumentMode` value (number); UXP
            // rejects the equivalent string literal.
            mode?: number;
            // Must be a `constants.DocumentFill` value (number).
            fill?: number;
            name?: string;
        }): Promise<PsDocument>;
    }

    export interface PhotoshopCore {
        executeAsModal<T>(
            fn: (executionContext: unknown) => Promise<T>,
            options?: { commandName?: string }
        ): Promise<T>;
        showAlert(opts: { message: string }): Promise<void>;
    }

    export interface PhotoshopConstants {
        LayerKind: {
            normal: number;
            group: number;
            smartObject: number;
            text: number;
            [key: string]: number;
        };
        TrimType: {
            TRANSPARENT: number;
            [key: string]: number;
        };
        // UXP rejects bare string mode names ("RGB" etc.); pass the
        // constant from `constants.NewDocumentMode.RGB`.
        NewDocumentMode: {
            RGB: number;
            CMYK: number;
            grayscale: number;
            [key: string]: number;
        };
        DocumentFill: {
            TRANSPARENT: number;
            WHITE: number;
            BACKGROUND_COLOR: number;
            [key: string]: number;
        };
        ElementPlacement: {
            PLACEATBEGINNING: number;
            PLACEATEND: number;
            INSIDE: number;
            [key: string]: number;
        };
    }

    export interface PsBounds {
        left: number;
        top: number;
        right: number;
        bottom: number;
    }

    /** UXP sometimes wraps numeric coordinates in a `UnitValue`-like
     *  object whose numeric payload lives on `value` or `_value`. The
     *  selection bounds reader handles both shapes. */
    export interface PsUnitNumber {
        readonly value?: number;
        readonly _value?: number;
    }

    /** Selection geometry reported by `PsDocument.selection`. Bounds may
     *  carry either plain numbers or `PsUnitNumber` wrappers depending
     *  on PS version. */
    export interface PsSelection {
        readonly bounds?: {
            readonly left?: number | PsUnitNumber;
            readonly top?: number | PsUnitNumber;
            readonly right?: number | PsUnitNumber;
            readonly bottom?: number | PsUnitNumber;
        };
    }

    export interface PsLayer {
        name: string;
        visible: boolean;
        readonly id: number;
        readonly bounds: PsBounds;
        readonly kind: number;
        readonly layers?: PsLayer[];
        /** Parent in the layer tree. Either an enclosing group layer
         *  or the host document when the layer sits at the root. */
        readonly parent?: PsLayer | PsDocument;
        /** XMP packet stamped onto the layer. PS 25 / CC 2024 exposes
         *  it as a string directly; some host builds nest it under
         *  `metadata.xmp`. See `src/io/xmp.ts` for the read / write
         *  contract. */
        xmpMetadata?: string;
        readonly metadata?: { xmp?: string };
        duplicate(target?: PsDocument | PsLayer): Promise<PsLayer>;
        // Translate accepts deltas in pixels (UnitValue-equivalent). UXP
        // also accepts plain numbers as pixels.
        translate(deltaX: number, deltaY: number): Promise<void>;
        delete(): Promise<void>;
        // Flatten a LayerSet's children into a single pixel layer.
        // No-op / error on art layers; we only call it on groups.
        merge(): Promise<PsLayer>;
        // Move into a different parent (group / document). Used to drop
        // a duplicated layer inside a LayerSet during sprite_frame import.
        move(parent: PsLayer | PsDocument, placement: number): Promise<void>;
    }

    export interface PsGuide {
        // UXP exposes guides as `{ direction: "horizontal" | "vertical", coordinate: number }`.
        // `coordinate` is in document pixels.
        readonly direction: "horizontal" | "vertical";
        readonly coordinate: number;
    }

    export interface PsDocument {
        readonly name: string;
        readonly width: number;
        readonly height: number;
        readonly layers: PsLayer[];
        readonly layerTree?: PsLayer[];
        /** The layers the user has selected. UXP reports an empty
         *  array when no selection exists; multiple entries when the
         *  user is multi-selecting in the Layers panel. */
        readonly activeLayers: PsLayer[];
        readonly saved: boolean;
        readonly path: string | null;
        readonly guides?: PsGuide[];
        /** Active marquee / lasso / region selection. Absent when the
         *  user has no selection; `bounds` is also optional because UXP
         *  reports the empty selection as `{ }` instead of clearing
         *  the field. */
        readonly selection?: PsSelection;
        trim(trimType: number, top?: boolean, bottom?: boolean, left?: boolean, right?: boolean): Promise<void>;
        closeWithoutSaving(): Promise<void>;
        // Create an empty layer group at the top of the stack.
        createLayerGroup(opts?: { name?: string }): Promise<PsLayer>;
        saveAs: {
            png(file: unknown, options?: { compression?: number; interlaced?: boolean }, copy?: boolean): Promise<void>;
            psd(file: unknown, options?: PsdSaveOptions, copy?: boolean): Promise<void>;
        };
    }

    export interface PsdSaveOptions {
        alphaChannels?: boolean;
        embedColorProfile?: boolean;
        layers?: boolean;
        spotColors?: boolean;
        annotations?: boolean;
        maximizeCompatibility?: boolean;
    }
}
