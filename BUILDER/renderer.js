document.addEventListener('DOMContentLoaded', () => {
    const buildButton = document.getElementById('buildButton');
    const c2UrlInput = document.getElementById('c2Url');
    const outputFileNameInput = document.getElementById('outputFileName');
    const iconFileInput = document.getElementById('iconFile');
    const selectedIconNameSpan = document.getElementById('selectedIconName');
    const statusMessage = document.getElementById('status-message');

    const outputDirectoryInput = document.getElementById('outputDirectory');
    const selectOutputDirectoryButton = document.getElementById('selectOutputDirectoryButton');
    
    const useUpxCheckbox = document.getElementById('useUpx');

    const themeToggle = document.getElementById('themeToggle');
    const langToggle = document.getElementById('langToggle');
    const htmlLang = document.getElementById('html-lang');
    const langElements = document.querySelectorAll('.lang-text');

    let currentLanguage = localStorage.getItem('builderLang') || 'en';
    let currentTheme = localStorage.getItem('builderTheme') || 'dark';

    const updateTheme = (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('builderTheme', theme);
    };

    const updateLanguage = (lang) => {
        htmlLang.lang = lang;
        langToggle.textContent = lang.toUpperCase();
        langElements.forEach(element => {
            element.textContent = element.dataset[lang];
        });
        localStorage.setItem('builderLang', lang);
    };

    updateTheme(currentTheme);
    updateLanguage(currentLanguage);

    themeToggle.addEventListener('click', () => {
        currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
        updateTheme(currentTheme);
    });

    langToggle.addEventListener('click', () => {
        currentLanguage = currentLanguage === 'en' ? 'ru' : 'en';
        updateLanguage(currentLanguage);
    });

    iconFileInput.addEventListener('change', () => {
        if (iconFileInput.files.length > 0) {
            selectedIconNameSpan.textContent = `Selected: ${iconFileInput.files[0].name}`;
        } else {
            selectedIconNameSpan.textContent = '';
        }
    });

    selectOutputDirectoryButton.addEventListener('click', async () => {
        const result = await window.electronAPI.showOpenDirectoryDialog();
        if (result && result.canceled === false && result.filePaths.length > 0) {
            outputDirectoryInput.value = result.filePaths[0];
        }
    });

    buildButton.addEventListener('click', () => {
        const c2Url = c2UrlInput.value.trim();
        const outputFileName = outputFileNameInput.value.trim();
        const iconPath = iconFileInput.files.length > 0 ? iconFileInput.files[0].path : '';
        const outputDirectory = outputDirectoryInput.value.trim();
        const useUpx = useUpxCheckbox.checked;

        if (!c2Url) {
            statusMessage.textContent = currentLanguage === 'en' ? 'Error: C2 URL cannot be empty.' : 'Ошибка: URL C2 сервера не может быть пустым.';
            statusMessage.className = 'status-error';
            return;
        }
        if (!outputFileName) {
            statusMessage.textContent = currentLanguage === 'en' ? 'Error: File name cannot be empty.' : 'Ошибка: Имя файла не может быть пустым.';
            statusMessage.className = 'status-error';
            return;
        }

        statusMessage.textContent = currentLanguage === 'en' ? 'BOFAMET: Starting build... Please wait.' : 'BOFAMET: Начинаю сборку... Пожалуйста, подождите.';
        statusMessage.className = ''; 

        window.electronAPI.buildMalware(c2Url, outputFileName, iconPath, outputDirectory, useUpx);
    });

    window.electronAPI.onBuildResult((args) => {
        const { success, message } = args;
        if (success) {
            statusMessage.textContent = `${currentLanguage === 'en' ? 'BOFAMET: Build successfully completed!' : 'BOFAMET: Сборка успешно завершена!'} ${message}`;
            statusMessage.className = 'status-success';
        } else {
            statusMessage.textContent = `${currentLanguage === 'en' ? 'BOFAMET: Build error!' : 'BOFAMET: Ошибка сборки!'} ${message}`;
            statusMessage.className = 'status-error';
        }
    });
});