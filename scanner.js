// simple-scanner.js - A standalone script for scanning project files
const fs = require('fs');
const path = require('path');

/**
 * Read all files in a directory recursively
 * @param {string} directoryPath - Directory to read
 * @param {RegExp|null} filter - Optional file filter regex
 * @param {Array<string>} exclude - Patterns to exclude
 * @returns {Object} - Object with file paths as keys and contents as values
 */
function scanDirectory(directoryPath, filter = null, exclude = ['.git', 'node_modules', 'dist', 'build']) {
    const result = {};
    
    function processDirectory(dirPath) {
        const entries = fs.readdirSync(dirPath, { withFileTypes: true });
        
        for (const entry of entries) {
            const fullPath = path.join(dirPath, entry.name);
            
            // Skip excluded directories/files
            if (exclude.some(pattern => entry.name === pattern || entry.name.startsWith(pattern + '/'))) {
                continue;
            }
            
            if (entry.isDirectory()) {
                processDirectory(fullPath);
            } else if (entry.isFile()) {
                // Apply filter if provided
                if (filter && !filter.test(entry.name)) {
                    continue;
                }
                
                try {
                    const content = fs.readFileSync(fullPath, 'utf8');
                    // Store relative path for cleaner output
                    const relativePath = path.relative(directoryPath, fullPath);
                    result[relativePath] = content;
                } catch (error) {
                    console.error(`Error reading file ${fullPath}:`, error);
                }
            }
        }
    }
    
    processDirectory(directoryPath);
    return result;
}

// Get current directory
const currentDir = process.cwd();

// Get filter argument if provided
const filterPattern = process.argv[2] ? new RegExp(process.argv[2]) : null;

console.log(`Scanning project in: ${currentDir}`);
if (filterPattern) {
    console.log(`Using filter pattern: ${process.argv[2]}`);
} else {
    console.log('Scanning all files (no filter specified)');
}

// Start scanning
try {
    const files = scanDirectory(currentDir, filterPattern);
    const fileCount = Object.keys(files).length;
    console.log(`Found ${fileCount} files`);
    
    // Create output directory
    const outputDir = path.join(currentDir, 'project_scan');
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir);
    }
    
    // Save file listing
    const fileListPath = path.join(outputDir, 'file_list.txt');
    fs.writeFileSync(
        fileListPath, 
        Object.keys(files).join('\n')
    );
    console.log(`File list saved to: ${fileListPath}`);
    
    // Save file contents
    const contentsPath = path.join(outputDir, 'file_contents.json');
    fs.writeFileSync(
        contentsPath,
        JSON.stringify(files, null, 2)
    );
    console.log(`File contents saved to: ${contentsPath}`);
    
    console.log('\nYou can now share the file_contents.json with Claude to get assistance with your code.');
} catch (error) {
    console.error('Error scanning project:', error);
}