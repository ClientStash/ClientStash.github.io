(() => {
    'use strict';

    const API_ROOT = 'https://countapi.mileshilliard.com/api/v1';
    const COUNTER_PREFIX = 'clientstash_download_v2_';

    function counterKey(productId) {
        return `${COUNTER_PREFIX}${productId}`;
    }

    function trackDownload(productId) {
        if (!productId) return;
        const url = `${API_ROOT}/hit/${encodeURIComponent(counterKey(productId))}`;
        fetch(url, { method: 'GET', mode: 'cors', cache: 'no-store', keepalive: true }).catch(() => {
            // Downloads must continue even when the public counter is unavailable.
        });
    }

    document.addEventListener('click', event => {
        const link = event.target.closest('a[data-download-product]');
        if (link) trackDownload(link.dataset.downloadProduct);
    }, { capture: true });

    window.ClientStashDownloadTracking = Object.freeze({ API_ROOT, COUNTER_PREFIX, counterKey });
})();
