/**
 * Lunii USB Transfer — Web File System Access API
 * 
 * Handles direct transfer of Lunii pack files to a connected Lunii device
 * via the browser's File System Access API (Chrome/Edge only).
 */

// Check if the browser supports the File System Access API
function isFileSystemAccessSupported() {
    return 'showDirectoryPicker' in window;
}

// Verify the selected directory is a Lunii device
async function isLuniiDevice(dirHandle) {
    try {
        // Check for .pi file (pack index) or .md metadata
        for await (const entry of dirHandle.values()) {
            if (entry.name === '.pi' || entry.name === '.md') {
                return true;
            }
        }
        // Also check for .content directory
        try {
            await dirHandle.getDirectoryHandle('.content');
            return true;
        } catch {
            return false;
        }
    } catch {
        return false;
    }
}

// Detect Lunii version from device files
async function detectLuniiVersion(dirHandle) {
    try {
        const mdHandle = await dirHandle.getFileHandle('.md');
        const mdFile = await mdHandle.getFile();
        const mdContent = await mdFile.text();

        if (mdContent.includes('v3') || mdContent.includes('V3')) {
            return 'V3';
        }
        return 'V2';
    } catch {
        return 'V2'; // Default
    }
}

// Read current pack index (.pi)
async function readPackIndex(dirHandle) {
    try {
        const piHandle = await dirHandle.getFileHandle('.pi');
        const piFile = await piHandle.getFile();
        const buffer = await piFile.arrayBuffer();
        return new Uint8Array(buffer);
    } catch {
        return new Uint8Array(0);
    }
}

// Update pack index with new UUID
async function updatePackIndex(dirHandle, packUuidBytes) {
    const existingData = await readPackIndex(dirHandle);

    // Combine existing + new UUID (16 bytes)
    const newData = new Uint8Array(existingData.length + packUuidBytes.length);
    newData.set(existingData, 0);
    newData.set(packUuidBytes, existingData.length);

    const piHandle = await dirHandle.getFileHandle('.pi', { create: true });
    const writable = await piHandle.createWritable();
    await writable.write(newData);
    await writable.close();
}

// Convert UUID string to 16-byte array
function uuidToBytes(uuidStr) {
    const hex = uuidStr.replace(/-/g, '');
    const bytes = new Uint8Array(16);
    for (let i = 0; i < 16; i++) {
        bytes[i] = parseInt(hex.substr(i * 2, 2), 16);
    }
    return bytes;
}

// Write a single file to device
async function writeFileToDevice(dirHandle, path, data) {
    const parts = path.split('/').filter(p => p.length > 0);
    let currentDir = dirHandle;

    // Create intermediate directories
    for (let i = 0; i < parts.length - 1; i++) {
        currentDir = await currentDir.getDirectoryHandle(parts[i], { create: true });
    }

    // Write file
    const fileName = parts[parts.length - 1];
    const fileHandle = await currentDir.getFileHandle(fileName, { create: true });
    const writable = await fileHandle.createWritable();
    await writable.write(data);
    await writable.close();
}

// Main transfer function — called from Streamlit via component
async function transferPack(zipBlobUrl, progressCallback) {
    try {
        // 1. Ask user to select Lunii device directory
        progressCallback(0, 'Sélection de l\'appareil Lunii...');
        const dirHandle = await window.showDirectoryPicker({
            mode: 'readwrite'
        });

        // 2. Verify it's a Lunii device
        progressCallback(0.05, 'Vérification de l\'appareil...');
        const isLunii = await isLuniiDevice(dirHandle);
        if (!isLunii) {
            throw new Error(
                'Le dossier sélectionné ne semble pas être un appareil Lunii. ' +
                'Veuillez sélectionner la racine de votre Lunii (contenant le dossier .content).'
            );
        }

        const version = await detectLuniiVersion(dirHandle);
        progressCallback(0.1, `Appareil Lunii ${version} détecté`);

        // 3. Fetch and unzip the pack
        progressCallback(0.15, 'Lecture du pack...');
        const response = await fetch(zipBlobUrl);
        const zipBlob = await response.blob();

        // Use JSZip to extract (loaded from CDN if needed)
        if (typeof JSZip === 'undefined') {
            await loadScript('https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js');
        }

        const zip = await JSZip.loadAsync(zipBlob);
        const entries = Object.keys(zip.files);

        // 4. Copy files to device
        const totalFiles = entries.filter(e => !zip.files[e].dir).length;
        let fileCount = 0;

        for (const entry of entries) {
            if (zip.files[entry].dir) continue;

            const data = await zip.files[entry].async('arraybuffer');
            await writeFileToDevice(dirHandle, entry, data);

            fileCount++;
            const progress = 0.2 + (0.7 * fileCount / totalFiles);
            progressCallback(progress, `Copie ${fileCount}/${totalFiles}: ${entry.split('/').pop()}`);
        }

        // 5. Update pack index
        progressCallback(0.95, 'Mise à jour de l\'index...');
        // Extract UUID from md file in the pack
        const mdEntry = entries.find(e => e.endsWith('/md'));
        if (mdEntry) {
            const mdText = await zip.files[mdEntry].async('text');
            const uuidMatch = mdText.match(/uuid:\s*([a-f0-9-]+)/i);
            if (uuidMatch) {
                const uuidBytes = uuidToBytes(uuidMatch[1]);
                await updatePackIndex(dirHandle, uuidBytes);
            }
        }

        progressCallback(1.0, '✅ Pack installé avec succès !');
        return { success: true, version: version };

    } catch (error) {
        if (error.name === 'AbortError') {
            progressCallback(0, 'Transfert annulé');
            return { success: false, error: 'Annulé par l\'utilisateur' };
        }
        progressCallback(0, `❌ Erreur: ${error.message}`);
        return { success: false, error: error.message };
    }
}

// Helper: dynamically load script
function loadScript(src) {
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = src;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

// Export for Streamlit component
window.LuniiTransfer = {
    isSupported: isFileSystemAccessSupported,
    transfer: transferPack,
    isLuniiDevice: isLuniiDevice,
    detectVersion: detectLuniiVersion
};
