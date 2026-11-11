const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('tracker', {
  snapshot: () => ipcRenderer.invoke('tracker:snapshot'),
  setSimilarity: (slug, status) => ipcRenderer.invoke('tracker:set-similarity', slug, status),
  setDealt: (slug, status) => ipcRenderer.invoke('tracker:set-dealt', slug, status),
  setCreativeFabricaDealt: (slug, status) => ipcRenderer.invoke('tracker:set-cf-dealt', slug, status),
  openLink: url => ipcRenderer.invoke('tracker:open-link', url),
  onProductsUpdated: callback => ipcRenderer.on('tracker:products-updated', () => callback())
});
