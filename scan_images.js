async function scanImages() {

    const images = {};
    try {
        const response = await fetch('manifest.json');
        if (response.ok) {
            const manifest = await response.json();
            Object.assign(images, manifest);
        } else {
            console.error('Failed to load manifest.json');
        }
    } catch (error) {
        console.error('Error fetching manifest:', error);
    }
    return images;
}

// Helper function to check if a folder is a battlepass
function isBattlepassFolder(folder) {
    return folder.endsWith('_battlepass');
}

// Helper function to check if a folder is an event
function isEventFolder(folder) {
    const contentFolders = {
        events: ['halloween', 'christmas_2024', 'summer'] // Keep in sync with the events array above
    };
    return contentFolders.events.includes(folder) || 
           contentFolders.events.some(event => folder === `${event}_battlepass`);
}

// Store the scanned images in localStorage to avoid rescanning on every page load
async function getOrScanImages() {
    const cachedImages = localStorage.getItem('scannedImages');
    if (cachedImages) {
        console.log('Loaded images from cache:', JSON.parse(cachedImages)); // Debugging: Check cached data
        return JSON.parse(cachedImages);
    }

    try {
        const response = await fetch('manifest.json');
        if (response.ok) {
            const manifest = await response.json();
            console.log('Loaded manifest.json:', manifest); // Debugging: Check fetched manifest
            localStorage.setItem('scannedImages', JSON.stringify(manifest));
            return manifest;
        } else {
            console.error('Failed to load manifest.json, status:', response.status);
        }
    } catch (error) {
        console.error('Error fetching manifest.json:', error);
    }

    return {}; // Return empty object if fetching fails
}

// Helper function to get active content folders (non-battlepass)
function getActiveContentFolders(images) {
    return Object.keys(images).filter(folder => 
        !isBattlepassFolder(folder)
    );
}

// Helper function to get battlepass folders
function getBattlepassFolders(images) {
    return Object.keys(images).filter(folder => 
        isBattlepassFolder(folder)
    );
}

// Helper function to get event folders
function getEventFolders(images) {
    return Object.keys(images).filter(folder => 
        isEventFolder(folder)
    );
}

// Helper function to get season folders
function getSeasonFolders(images) {
    return Object.keys(images).filter(folder => 
        !isEventFolder(folder) && !isBattlepassFolder(folder)
    );
} 