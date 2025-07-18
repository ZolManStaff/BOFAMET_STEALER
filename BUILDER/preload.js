const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    buildMalware: (c2Url, outputFileName, iconPath, outputDirectory, useUpx) => ipcRenderer.send('build-malware', { c2Url, outputFileName, iconPath, outputDirectory, useUpx }),
    onBuildResult: (callback) => ipcRenderer.on('build-result', (event, args) => callback(args)),
    showOpenDirectoryDialog: () => ipcRenderer.invoke('show-open-directory-dialog') 
}); 