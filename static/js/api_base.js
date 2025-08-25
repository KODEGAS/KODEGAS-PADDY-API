/* Centralized API base detection for the static UI
   Sets window.API_BASE to either a relative path (for localhost),
   the current origin (when UI and API are served from same host),
   or a fallback production URL.
*/
(function () {
    function getApiBase() {
        const host = window.location.hostname;
        const port = window.location.port ? (':' + window.location.port) : '';

        // Local dev: use relative paths
        if (host === '127.0.0.1' || host === 'localhost') {
            return '';
        }

        // For the Azure VM host, force http scheme (explicit requirement)
        if (host === 'kodegas-paddy-api.centralindia.cloudapp.azure.com') {
            return 'http://' + host + port;
        }

        // Otherwise prefer the current origin (same-origin deployments)
        if (window.location.origin) {
            return window.location.origin;
        }

        // Fallback to the explicit http host
        return 'http://kodegas-paddy-api.centralindia.cloudapp.azure.com';
    }

    window.API_BASE = getApiBase();
})();
