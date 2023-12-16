import { app, BrowserWindow, screen, dialog, ipcMain } from 'electron'
import electronSquirrelStartup from 'electron-squirrel-startup';

// some Windows-update-related shit
if (electronSquirrelStartup) app.quit();

let destroyed = false
let interrupted = false

process.on('SIGINT', () => {
    interrupted = true
});
process.on('SIGTERM', () => {
    interrupted = true
});

const createWindow = () => {
    const mainWindow = new BrowserWindow({
        autoHideMenuBar: true,
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
        },
    })

    const currentScreen = screen.getDisplayNearestPoint(screen.getCursorScreenPoint())
    let screenOrigin = currentScreen.nativeOrigin;
    let screenSize = currentScreen.size;
    mainWindow.setPosition(
        screenOrigin.x + (screenSize.width - mainWindow.getSize()[0]) / 2,
        screenOrigin.y + (screenSize.height - mainWindow.getSize()[1]) / 2)

    mainWindow.loadFile('build/index.html', {
        query: {
            isPackaged: app.isPackaged,
            appPath: app.getAppPath(),
            argv: process.argv,
        }
    })

    let destroyable = false
    mainWindow.on('close', (e) => {
        if (destroyable && !destroyed) {
            mainWindow.webContents.send('destroy', interrupted);
            e.preventDefault();
        }
    });

    ipcMain.on('set-destroyable', () => {
        destroyable = true
    })

    ipcMain.on('ask', (evt, cb, title, message, buttons) => {
        const response = dialog.showMessageBoxSync(mainWindow, {
            type: 'question',
            title: title,
            message: message,
            buttons: buttons,
        })

        mainWindow.webContents.send(cb, response);
    })
}

app.whenReady().then(() => {
    createWindow()
})

app.on('window-all-closed', () => {
    app.quit()
})

ipcMain.on('destroyed', (evt) => {
    destroyed = true
    app.quit()
})
