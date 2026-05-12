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

    export interface LocalFileSystem {
        getFolder(): Promise<UxpFolder>;
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
    }
}

declare module "photoshop" {
    export const app: PhotoshopApp;
    export const core: PhotoshopCore;
    export const constants: PhotoshopConstants;
    export const action: {
        batchPlay(commands: unknown[], options?: unknown): Promise<unknown>;
    };

    export interface PhotoshopApp {
        activeDocument: PsDocument | null;
        documents: PsDocumentCollection;
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
    }

    export interface PsBounds {
        left: number;
        top: number;
        right: number;
        bottom: number;
    }

    export interface PsLayer {
        readonly name: string;
        readonly visible: boolean;
        readonly bounds: PsBounds;
        readonly kind: number;
        readonly layers?: PsLayer[];
        duplicate(target?: PsDocument): Promise<PsLayer>;
        delete(): Promise<void>;
    }

    export interface PsDocument {
        readonly name: string;
        readonly width: number;
        readonly height: number;
        readonly layers: PsLayer[];
        readonly saved: boolean;
        readonly path: string | null;
        trim(trimType: number, top?: boolean, bottom?: boolean, left?: boolean, right?: boolean): Promise<void>;
        closeWithoutSaving(): Promise<void>;
        saveAs: {
            png(file: unknown, options?: { compression?: number; interlaced?: boolean }, copy?: boolean): Promise<void>;
        };
    }
}
