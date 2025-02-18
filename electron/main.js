const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const isDev = require('electron-is-dev');
const portfinder = require('portfinder');

let mainWindow;
let pythonProcess;

async function createWindow() {
    // Find an available port for the Python backend
    const port = await portfinder.getPortPromise();

    // Start Python backend
    const pythonExecutable = path.join(app.getAppPath(), 'backend', 'venv', 'Scripts', 'python.exe');
    const pythonScript = path.join(app.getAppPath(), 'backend', 'app', 'main.py');
    
    pythonProcess = spawn(pythonExecutable, [pythonScript, '--port', port.toString()], {
        stdio: 'pipe'
    });

    pythonProcess.stdout.on('data', (data) => {
        console.log(`Python stdout: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`Python stderr: ${data}`);
    });

    // Create the browser window
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    // Load the app
    if (isDev) {
        mainWindow.loadURL('http://localhost:3000');
        mainWindow.webContents.openDevTools();
    } else {
        mainWindow.loadFile(path.join(__dirname, '../frontend/build/index.html'));
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        if (pythonProcess) {
            pythonProcess.kill();
        }
        app.quit();
    }
});

app.on('activate', () => {
    if (mainWindow === null) {
        createWindow();
    }
});
