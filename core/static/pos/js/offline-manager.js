/**
 * POS Offline Manager
 * Handles IndexedDB storage for products, categories, and offline transactions.
 */

class OfflineManager {
    constructor() {
        this.dbName = 'SalesCompassPOS';
        this.dbVersion = 1;
        this.db = null;
        this.isOnline = navigator.onLine;
        this.syncInterval = 30000; // 30 seconds
    }

    async init() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);

            request.onupgradeneeded = (event) => {
                const db = event.target.result;

                // Products Store
                if (!db.objectStoreNames.contains('products')) {
                    const productStore = db.createObjectStore('products', { keyPath: 'id' });
                    productStore.createIndex('name', 'name', { unique: false });
                    productStore.createIndex('category', 'category_id', { unique: false });
                    productStore.createIndex('barcode', 'barcode', { unique: false });
                }

                // Categories Store
                if (!db.objectStoreNames.contains('categories')) {
                    db.createObjectStore('categories', { keyPath: 'id' });
                }

                // Offline Transactions Store
                if (!db.objectStoreNames.contains('offline_transactions')) {
                    db.createObjectStore('offline_transactions', { keyPath: 'tempId', autoIncrement: true });
                }

                // Customers Store
                if (!db.objectStoreNames.contains('customers')) {
                    const customerStore = db.createObjectStore('customers', { keyPath: 'id' });
                    customerStore.createIndex('name', 'name', { unique: false });
                }
            };

            request.onsuccess = (event) => {
                this.db = event.target.result;
                this.setupConnectivityListeners();
                this.updateStatusUI();
                resolve();
            };

            request.onerror = (event) => reject(event.target.error);
        });
    }

    setupConnectivityListeners() {
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.updateStatusUI();
            this.syncData();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.updateStatusUI();
        });
    }

    updateStatusUI() {
        const statusDot = document.getElementById('connectivity-status-dot');
        const statusText = document.getElementById('connectivity-status-text');

        if (statusDot && statusText) {
            if (this.isOnline) {
                statusDot.classList.remove('bg-danger');
                statusDot.classList.add('bg-success');
                statusText.textContent = 'Online';
            } else {
                statusDot.classList.remove('bg-success');
                statusDot.classList.add('bg-danger');
                statusText.textContent = 'Offline';
            }
        }
    }

    // Product Methods
    async saveProducts(products) {
        if (!products || !products.length) return;
        const tx = this.db.transaction('products', 'readwrite');
        const store = tx.objectStore('products');
        products.forEach(p => store.put(p));
        return new Promise((resolve) => {
            tx.oncomplete = () => resolve();
        });
    }

    async getProducts(query = '', categoryId = '') {
        return new Promise((resolve) => {
            const tx = this.db.transaction('products', 'readonly');
            const store = tx.objectStore('products');
            const request = store.getAll();

            request.onsuccess = () => {
                let products = request.result;
                if (categoryId) {
                    products = products.filter(p => p.category_id == categoryId);
                }
                if (query) {
                    const q = query.toLowerCase();
                    products = products.filter(p =>
                        (p.name && p.name.toLowerCase().includes(q)) ||
                        (p.sku && p.sku.toLowerCase().includes(q)) ||
                        (p.barcode && p.barcode.toLowerCase().includes(q))
                    );
                }
                resolve(products);
            };
        });
    }

    // Category Methods
    async saveCategories(categories) {
        if (!categories || !categories.length) return;
        const tx = this.db.transaction('categories', 'readwrite');
        const store = tx.objectStore('categories');
        categories.forEach(c => store.put(c));
        return new Promise((resolve) => {
            tx.oncomplete = () => resolve();
        });
    }

    async getCategories() {
        return new Promise((resolve) => {
            const tx = this.db.transaction('categories', 'readonly');
            const store = tx.objectStore('categories');
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result);
        });
    }

    // Transaction Methods
    async saveOfflineTransaction(txn) {
        const tx = this.db.transaction('offline_transactions', 'readwrite');
        const store = tx.objectStore('offline_transactions');
        txn.timestamp = new Date().toISOString();
        txn.synced = false;
        return new Promise((resolve) => {
            const request = store.add(txn);
            request.onsuccess = () => resolve(request.result);
        });
    }

    async getPendingTransactions() {
        return new Promise((resolve) => {
            const tx = this.db.transaction('offline_transactions', 'readonly');
            const store = tx.objectStore('offline_transactions');
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result.filter(t => !t.synced));
        });
    }

    async markSynced(tempId) {
        const tx = this.db.transaction('offline_transactions', 'readwrite');
        const store = tx.objectStore('offline_transactions');
        const request = store.get(tempId);
        request.onsuccess = () => {
            const data = request.result;
            if (data) {
                data.synced = true;
                store.put(data);
            }
        };
    }

    async syncData() {
        if (!this.isOnline) return;

        const pending = await this.getPendingTransactions();
        if (pending.length === 0) return;

        console.log(`Syncing ${pending.length} offline transactions...`);

        for (const txn of pending) {
            try {
                const response = await fetch('/pos/api/transactions/sync-offline/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': CSRF_TOKEN
                    },
                    body: JSON.stringify(txn)
                });

                if (response.ok) {
                    await this.markSynced(txn.tempId);
                }
            } catch (err) {
                console.error('Sync failed for transaction', txn, err);
            }
        }
    }
}

window.offlineManager = new OfflineManager();
document.addEventListener('DOMContentLoaded', () => {
    window.offlineManager.init().then(() => {
        console.log('Offline Manager initialized');
        if (window.offlineManager.isOnline) {
            window.offlineManager.syncData();
        }
    });
});
