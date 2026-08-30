/**
 * Lemma Central API Configuration Engine
 * Seamlessly supports localhost, same-origin, custom backend URLs, and Netlify/Vercel deployments.
 */
window.LEMMA_CONFIG = window.LEMMA_CONFIG || {
    API_BASE_URL: ''
};

const APIConfigManager = {
    STORAGE_KEY: 'lemma_override_api_url',

    /**
     * Resolves the primary URL used to reach the FastAPI backend.
     */
    async getApiBaseUrl() {
        // 1. Explicit global window config
        if (window.LEMMA_CONFIG && window.LEMMA_CONFIG.API_BASE_URL) {
            return window.LEMMA_CONFIG.API_BASE_URL.replace(/\/$/, '');
        }

        // 2. Local developer override in LocalStorage
        const localOverride = localStorage.getItem(this.STORAGE_KEY);
        if (localOverride) {
            return localOverride.replace(/\/$/, '');
        }

        // 3. Check for runtime config.json
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 1000);
            const response = await fetch('config.json', { signal: controller.signal });
            clearTimeout(timeoutId);
            
            if (response.ok) {
                const configData = await response.json();
                if (configData.BACKEND_API_URL) {
                    return configData.BACKEND_API_URL.replace(/\/$/, '');
                }
            }
        } catch (e) {
            // Ignore fetch error
        }

        // 4. Same origin if served from FastAPI server or localhost
        const host = window.location.hostname;
        if (host === 'localhost' || host === '127.0.0.1') {
            if (window.location.port === '8000') {
                return window.location.origin;
            }
            return 'http://localhost:8000';
        }

        // 5. Default to same origin if available, otherwise localhost
        if (window.location.origin && window.location.origin.startsWith('http')) {
            return window.location.origin;
        }

        return 'http://localhost:8000';
    },

    setDeveloperOverrideUrl(url) {
        if (!url) {
            localStorage.removeItem(this.STORAGE_KEY);
            return;
        }
        localStorage.setItem(this.STORAGE_KEY, url.trim().replace(/\/$/, ''));
    }
};
