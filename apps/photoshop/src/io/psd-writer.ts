// PSD save helper. Mirrors the JSX importer's tail step: write the
// reconstructed document to `<manifestFolder>/photoshop/<docName>` so
// the fixture layout matches the existing convention (manifest at
// root, PSD under `photoshop/`).

import type { PsDocument } from "photoshop";
import type { UxpFile, UxpFolder } from "uxp";

export async function savePsd(
    doc: PsDocument,
    folder: UxpFolder,
    fileName: string,
): Promise<UxpFile> {
    const photoshopDir = await ensureSubfolder(folder, "photoshop");
    const file = await photoshopDir.createFile(fileName, { overwrite: true });
    await doc.saveAs.psd(
        file,
        {
            alphaChannels: true,
            embedColorProfile: true,
            layers: true,
            spotColors: false,
            maximizeCompatibility: true,
        },
        false,
    );
    return file;
}

async function ensureSubfolder(parent: UxpFolder, name: string): Promise<UxpFolder> {
    try {
        return await parent.createFolder(name, { overwrite: false });
    } catch {
        // Folder already exists - look it up and confirm it really is
        // a folder. A file at the same path would otherwise be cast
        // to UxpFolder and break downstream calls.
        const entry = await parent.getEntry(name);
        if (!entry.isFolder) {
            throw new Error(`output path collides with a non-folder entry: ${name}`);
        }
        return entry as UxpFolder;
    }
}
