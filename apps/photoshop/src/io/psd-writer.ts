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
        return (await parent.getEntry(name)) as UxpFolder;
    }
}
