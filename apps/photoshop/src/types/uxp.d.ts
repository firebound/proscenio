// Minimal ambient module shims for UXP / Photoshop runtime modules.
//
// Adobe does not publish `@types/uxp` or `@types/photoshop` on npm; the
// real type bundles ship with the UDT (UXP Developer Tool) install and
// are sourced from the local Photoshop UXP runtime at debug-load time.
// These shims keep `tsc --noEmit` honest until the real types land --
// they intentionally widen the surface to `unknown` (not `any`) for
// the bits we have not exercised yet, so call sites still feel the
// type pressure of an unknown shape.
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
		localFileSystem: {
			getFolder(): Promise<UxpFolder>;
		};
	};

	export interface UxpFolder {
		createFile(name: string, options?: { overwrite?: boolean }): Promise<UxpFile>;
		createFolder(name: string): Promise<UxpFolder>;
	}

	export interface UxpFile {
		write(contents: string | ArrayBuffer): Promise<void>;
		read(): Promise<string>;
	}
}

declare module "photoshop" {
	export const app: {
		activeDocument: unknown;
		documents: unknown[];
	};

	export const action: {
		batchPlay(commands: unknown[], options?: unknown): Promise<unknown>;
	};
}
