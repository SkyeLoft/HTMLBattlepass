async function scanImages() {
    const images = {};
    
    // Define your content folders
    const contentFolders = {
        seasons: ['season1', 'season2', 'season3'], // Add your seasons
        events: ['halloween', 'christmas', 'summer'] // Add your events
    };
    
    const extensions = ['jpg', 'jpeg', 'png', 'gif'];
    const maxImagesPerFolder = 100; // Adjust based on your needs

    // Scan season folders
    for (const season of contentFolders.seasons) {
        // Regular season folder
        images[season] = [];
        // Battlepass folder
        images[`${season}_battlepass`] = [];

        // Scan both regular and battlepass folders
        for (const folder of [season, `${season}_battlepass`]) {
            // Try images with different extensions and numbers
            for (let i = 1; i <= maxImagesPerFolder; i++) {
                for (const ext of extensions) {
                    const imagePath = `images/${folder}/image${i}.${ext}`;
                    try {
                        const response = await fetch(imagePath, { method: 'HEAD' });
                        if (response.ok) {
                            images[folder].push(`image${i}.${ext}`);
                        }
                    } catch (error) {
                        continue;
                    }
                }
            }
        }

        // Remove empty folders
        if (images[season].length === 0) delete images[season];
        if (images[`${season}_battlepass`].length === 0) delete images[`${season}_battlepass`];
    }

    // Scan event folders
    for (const event of contentFolders.events) {
        // Regular event folder
        images[event] = [];
        // Event battlepass folder (if you have event battlepasses)
        images[`${event}_battlepass`] = [];

        // Scan both regular and battlepass folders
        for (const folder of [event, `${event}_battlepass`]) {
            // Try images with different extensions and numbers
            for (let i = 1; i <= maxImagesPerFolder; i++) {
                for (const ext of extensions) {
                    const imagePath = `images/${folder}/image${i}.${ext}`;
                    try {
                        const response = await fetch(imagePath, { method: 'HEAD' });
                        if (response.ok) {
                            images[folder].push(`image${i}.${ext}`);
                        }
                    } catch (error) {
                        continue;
                    }
                }
            }
        }

        // Remove empty folders
        if (images[event].length === 0) delete images[event];
        if (images[`${event}_battlepass`].length === 0) delete images[`${event}_battlepass`];
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
        events: ['halloween', 'christmas', 'summer'] // Keep in sync with the events array above
    };
    return contentFolders.events.includes(folder) || 
           contentFolders.events.some(event => folder === `${event}_battlepass`);
}

// Store the scanned images in localStorage to avoid rescanning on every page load
async function getOrScanImages() {
    const cachedImages = localStorage.getItem('scannedImages');
    if (cachedImages) {
        return JSON.parse(cachedImages);
    }

    const images = await scanImages();
    localStorage.setItem('scannedImages', JSON.stringify(images));
    return images;
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