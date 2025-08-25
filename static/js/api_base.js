/* Centralized API base detection for the static UI
   Sets window.API_BASE to either a relative path (for localhost),
   the current origin (when UI and API are served from same host),
   or a fallback production URL.
*/
(function () {
    function getApiBase() {
        if (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost') {
            return '';
        }
        if (window.location.origin) {
            return window.location.origin;
        }
        return 'http://kodegas-paddy-api.centralindia.cloudapp.azure.com';
    }

    window.API_BASE = getApiBase();
})();
