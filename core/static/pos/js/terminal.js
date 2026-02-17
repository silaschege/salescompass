/* POS Terminal Logic - Enhanced */

let currentCategory = '';
let searchTimeout = null;
let currentProducts = [];

document.addEventListener('DOMContentLoaded', function () {
    loadProducts();
    loadCart();

    // Search Input
    const searchInput = document.getElementById('product-search');
    if (searchInput) {
        searchInput.addEventListener('input', function (e) {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                loadProducts(e.target.value, currentCategory);
            }, 300);
        });
    }

    // Fullscreen Toggle
    const fsBtn = document.getElementById('fullscreen-btn');
    if (fsBtn) {
        fsBtn.addEventListener('click', function () {
            if (!document.fullscreenElement) {
                document.documentElement.requestFullscreen();
                fsBtn.innerHTML = '<i class="bi bi-arrows-angle-contract"></i>';
            } else {
                if (document.exitFullscreen) {
                    document.exitFullscreen();
                    fsBtn.innerHTML = '<i class="bi bi-arrows-fullscreen"></i>';
                }
            }
        });
    }

    // Cart Action Buttons
    const clearBtn = document.getElementById('clear-cart-btn');
    if (clearBtn) clearBtn.addEventListener('click', clearCart);

    const holdBtn = document.getElementById('hold-btn');
    if (holdBtn) holdBtn.addEventListener('click', holdTransaction);

    // Barcode Listener (Global)
    let barcodeBuffer = '';
    let lastKeyTime = Date.now();

    document.addEventListener('keydown', function (e) {
        // Simple barcode scanner detection (rapid input)
        const currentTime = Date.now();
        if (currentTime - lastKeyTime > 100) {
            barcodeBuffer = '';
        }
        lastKeyTime = currentTime;

        if (e.key === 'Enter') {
            if (barcodeBuffer.length > 2) {
                handleBarcodeScan(barcodeBuffer);
                barcodeBuffer = '';
                e.preventDefault();
            }
        } else if (e.key.length === 1 && !e.ctrlKey && !e.altKey) {
            barcodeBuffer += e.key;
        }
    });

    // Start stock polling
    if (typeof pollStockLevels === 'function') {
        setInterval(pollStockLevels, 30000);
    }
});

function loadProducts(query = '', categoryId = '') {
    currentCategory = categoryId;

    const container = document.getElementById('product-grid-container');
    const row = container.querySelector('.row');

    let url = '';
    if (query.length >= 2) {
        url = `/pos/api/products/search/?q=${encodeURIComponent(query)}`;
        if (categoryId) {
            url += `&category=${categoryId}`;
        }
    } else {
        url = `/pos/api/products/`;
        if (categoryId) {
            url += `?category=${categoryId}`;
        }
    }


    fetch(url)
        .then(response => response.json())
        .then(data => {
            row.innerHTML = '';
            currentProducts = data.products || [];

            if (currentProducts.length === 0) {
                row.innerHTML = '<div class="col-12 text-center py-5 text-muted">No products found.</div>';
                return;
            }

            currentProducts.forEach(product => {
                const card = createProductCard(product);
                row.appendChild(card);
            });

            // Poll stock immediately after loading new products
            if (typeof pollStockLevels === 'function') {
                pollStockLevels();
            }
        })
        .catch(err => console.error('Error loading products:', err));
}

function createProductCard(product) {
    const col = document.createElement('div');
    col.className = 'col';
    col.dataset.productId = product.id;

    const price = parseFloat(product.price);

    col.innerHTML = `
        <div class="card h-100 product-card shadow-sm" onclick="addToCart(${product.id})">
            <div class="product-image">
                ${product.image ? `<img src="${product.image}" alt="${product.name}" loading="lazy">` : '<i class="bi bi-box placeholder-icon"></i>'}
            </div>
            <div class="product-info">
                <div class="product-name" title="${product.name}">${product.name}</div>
                <div class="product-sku text-muted small">${product.sku}</div>
                <div class="d-flex justify-content-between align-items-center mt-2">
                    <div class="product-price text-primary fw-bold">${formatCurrency(price)}</div>
                    <small class="product-stock text-muted" data-product-id="${product.id}">Checking...</small>
                </div>
            </div>
        </div>
    `;
    return col;
}

function addToCart(productId) {
    fetch(`/pos/api/transactions/${TRANSACTION_ID}/lines/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF_TOKEN
        },
        body: JSON.stringify({ product_id: productId, quantity: 1 })
    })
        .then(response => response.json())
        .then(data => {
            if (data.id) {
                loadCart();
                playSuccessSound();
                showToast(`Added to cart`, 'success');
            } else {
                showToast(data.error || 'Error adding product', 'error');
            }
        })
        .catch(err => {
            console.error('Error adding to cart:', err);
            showToast('Network error', 'error');
        });
}

function loadCart() {
    fetch(`/pos/api/transactions/${TRANSACTION_ID}/`)
        .then(response => response.json())
        .then(data => {
            updateCartUI(data);
        })
        .catch(err => console.error('Error loading cart:', err));
}

function updateCartUI(transaction) {
    const container = document.getElementById('cart-items-container');
    const checkoutBtn = document.getElementById('checkout-btn');
    const holdBtn = document.getElementById('hold-btn');
    const clearBtn = document.getElementById('clear-cart-btn');

    if (!transaction.lines || transaction.lines.length === 0) {
        container.innerHTML = `
            <div class="empty-cart">
                <i class="bi bi-cart-x empty-cart-icon"></i>
                <p class="empty-cart-text">No items in cart</p>
                <small class="text-muted">Select products to start</small>
            </div>`;
        if (checkoutBtn) checkoutBtn.disabled = true;
        if (holdBtn) holdBtn.disabled = true;
        if (clearBtn) clearBtn.disabled = true;
    } else {
        container.innerHTML = '';
        transaction.lines.forEach(line => {
            const item = document.createElement('div');
            item.className = 'cart-item d-flex align-items-center';
            item.dataset.lineId = line.id;

            const lineTotal = parseFloat(line.line_total);
            const unitPrice = parseFloat(line.unit_price);

            item.innerHTML = `
                <div class="cart-item-info flex-grow-1">
                    <div class="cart-item-name">${line.product_name}</div>
                    <div class="cart-item-price">${formatCurrency(unitPrice)} each</div>
                </div>
                <div class="cart-item-qty d-flex align-items-center gap-2 mx-3">
                    <button class="qty-btn" onclick="updateQty(${line.id}, -1)">
                        <i class="bi bi-dash"></i>
                    </button>
                    <span class="qty-value">${Math.round(line.quantity)}</span>
                    <button class="qty-btn" onclick="updateQty(${line.id}, 1)">
                        <i class="bi bi-plus"></i>
                    </button>
                </div>
                <div class="cart-item-total fw-bold me-2" style="min-width: 80px; text-align: right;">
                    ${formatCurrency(lineTotal)}
                </div>
                <button class="btn btn-sm btn-outline-danger border-0" onclick="removeFromCart(${line.id})">
                    <i class="bi bi-trash"></i>
                </button>
            `;
            container.appendChild(item);
        });
        if (checkoutBtn) checkoutBtn.disabled = false;
        if (holdBtn) holdBtn.disabled = false;
        if (clearBtn) clearBtn.disabled = false;
    }

    // Update Summary
    updateSummaryUI(transaction);
}

function updateSummaryUI(transaction) {
    const subtotal = document.getElementById('cart-subtotal');
    const tax = document.getElementById('cart-tax');
    const total = document.getElementById('cart-total');
    const discount = document.getElementById('cart-discount');

    if (subtotal) subtotal.textContent = formatCurrency(parseFloat(transaction.subtotal || 0));
    if (tax) tax.textContent = formatCurrency(parseFloat(transaction.tax_amount || 0));
    if (total) total.textContent = formatCurrency(parseFloat(transaction.total || transaction.total_amount || 0));
    if (discount) {
        const discAmt = parseFloat(transaction.discount_amount || 0);
        if (discAmt > 0) {
            discount.parentElement.style.display = 'flex';
            discount.textContent = `-${formatCurrency(discAmt)}`;
        } else {
            discount.parentElement.style.display = 'none';
        }
    }
}

function updateQty(lineId, delta) {
    // Optimization: find line locally first to get current qty
    const lineRow = document.querySelector(`.cart-item[data-line-id="${lineId}"]`);
    if (!lineRow) return;

    const qtySpan = lineRow.querySelector('.qty-value');
    const currentQty = parseFloat(qtySpan.textContent);
    const newQty = Math.max(1, currentQty + delta);

    if (newQty === currentQty) return;

    qtySpan.textContent = newQty;
    lineRow.classList.add('product-highlight');

    fetch(`/pos/api/transactions/${TRANSACTION_ID}/lines/${lineId}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
        body: JSON.stringify({ quantity: newQty })
    })
        .then(res => res.json())
        .then(data => {
            if (data.id || data.success) {
                loadCart();
            } else {
                qtySpan.textContent = currentQty;
                showToast(data.error || 'Failed to update quantity', 'error');
            }
        })
        .catch(err => {
            qtySpan.textContent = currentQty;
            showToast('Network error', 'error');
        })
        .finally(() => {
            setTimeout(() => lineRow.classList.remove('product-highlight'), 500);
        });
}

function removeFromCart(lineId) {
    if (!confirm('Remove this item?')) return;

    fetch(`/pos/api/transactions/${TRANSACTION_ID}/lines/${lineId}/`, {
        method: 'DELETE',
        headers: { 'X-CSRFToken': CSRF_TOKEN }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadCart();
                showToast('Item removed', 'info');
            }
        });
}

function clearCart() {
    if (!confirm('Clear all items from the cart?')) return;

    fetch(`/pos/api/transactions/${TRANSACTION_ID}/clear/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': CSRF_TOKEN }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadCart();
                showToast('Cart cleared', 'info');
            }
        });
}

function holdTransaction() {
    if (!confirm('Put this transaction on hold?')) return;

    fetch(`/pos/api/transactions/${TRANSACTION_ID}/hold/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': CSRF_TOKEN }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showToast('Transaction put on hold', 'info');
                setTimeout(() => window.location.href = '/pos/terminal/', 1000);
            }
        });
}

function showSavedOrders() {
    const modal = new bootstrap.Modal(document.getElementById('heldOrdersModal'));
    const list = document.getElementById('held-orders-list');
    const empty = document.getElementById('held-orders-empty');

    list.innerHTML = '<tr><td colspan="6" class="text-center py-4"><div class="spinner-border spinner-border-sm text-primary"></div> Loading...</td></tr>';
    empty.classList.add('d-none');
    modal.show();

    fetch('/pos/api/transactions/held/')
        .then(res => res.json())
        .then(data => {
            list.innerHTML = '';
            if (!data.transactions || data.transactions.length === 0) {
                empty.classList.remove('d-none');
                return;
            }

            data.transactions.forEach(txn => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td><strong>${txn.transaction_number}</strong></td>
                    <td>${txn.customer_name || '—'}</td>
                    <td>${txn.items_count}</td>
                    <td>${formatCurrency(txn.total)}</td>
                    <td><small>${txn.held_at}</small></td>
                    <td class="text-end">
                        <button class="btn btn-sm btn-primary" onclick="resumeTransaction(${txn.id})">
                            Resume
                        </button>
                    </td>
                `;
                list.appendChild(row);
            });
        });
}

function resumeTransaction(id) {
    if (!confirm('Resume this transaction? Current cart will be lost.')) return;

    fetch(`/pos/api/transactions/${id}/resume/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': CSRF_TOKEN }
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                window.location.href = `/pos/terminal/?transaction_id=${data.id}`;
            } else {
                showToast(data.error || 'Failed to resume transaction', 'error');
            }
        });
}

function handleBarcodeScan(barcode) {
    fetch(`/pos/api/products/barcode/${barcode}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                addToCart(data.product.id);
            } else {
                showToast('Product not found: ' + barcode, 'error');
            }
        });
}

/* Payment Handling */
let selectedPaymentMethod = 'cash';
let tenderedAmount = 0;

function initPaymentLogic() {
    // Payment Method selection
    const methodBtns = document.querySelectorAll('.payment-method-btn');
    methodBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            methodBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            selectedPaymentMethod = this.dataset.method;

            // Toggle visibility of reference input
            const refSection = document.getElementById('reference-input-section');
            const cashSection = document.getElementById('cash-input-section');

            if (selectedPaymentMethod === 'cash') {
                if (refSection) refSection.classList.add('d-none');
                if (cashSection) cashSection.classList.remove('d-none');
            } else {
                if (refSection) refSection.classList.remove('d-none');
                if (cashSection) cashSection.classList.add('d-none');
            }
        });
    });

    // Cash input handling
    const cashInput = document.getElementById('cash-amount');
    if (cashInput) {
        cashInput.addEventListener('input', function () {
            tenderedAmount = parseFloat(this.value) || 0;
            updatePaymentDetails();
        });
    }

    // Quick amounts
    const quickAmountBtns = document.querySelectorAll('.quick-amount');
    quickAmountBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            const amount = this.dataset.amount;
            const dueText = document.getElementById('payment-amount-due').textContent;
            const totalDue = parseFloat(dueText.replace(/[^0-9.]/g, ''));

            if (amount === 'exact') {
                tenderedAmount = totalDue;
            } else {
                tenderedAmount = parseFloat(amount);
            }

            if (cashInput) cashInput.value = tenderedAmount;
            updatePaymentDetails();
        });
    });

    // Complete Payment
    const completePaymentBtn = document.getElementById('complete-payment-btn');
    if (completePaymentBtn) {
        completePaymentBtn.addEventListener('click', completePayment);
    }
}

function updatePaymentDetails() {
    const dueEl = document.getElementById('payment-amount-due');
    if (!dueEl) return;

    const totalDue = parseFloat(dueEl.textContent.replace(/[^0-9.]/g, ''));
    const tenderedEl = document.getElementById('payment-tendered');
    const changeEl = document.getElementById('payment-change');

    if (tenderedEl) tenderedEl.textContent = formatCurrency(tenderedAmount);
    const change = Math.max(0, tenderedAmount - totalDue);
    if (changeEl) changeEl.textContent = formatCurrency(change);
}

function completePayment() {
    const splitPaymentCheck = document.getElementById('split-payment-check');
    const isSplit = splitPaymentCheck ? splitPaymentCheck.checked : false;

    let amount;
    if (selectedPaymentMethod === 'cash') {
        amount = tenderedAmount;
    } else {
        const dueEl = document.getElementById('payment-amount-due');
        amount = parseFloat(dueEl.textContent.replace(/[^0-9.]/g, ''));
    }

    if (amount <= 0) {
        showToast('Please enter a valid amount', 'error');
        return;
    }

    const reference = document.getElementById('payment-reference') ? document.getElementById('payment-reference').value : '';

    const payload = {
        payment_methods: [{
            method: selectedPaymentMethod,
            amount: amount,
            reference_number: reference
        }]
    };

    const checkoutBtn = document.getElementById('complete-payment-btn');
    if (checkoutBtn) checkoutBtn.disabled = true;

    fetch(`/pos/api/transactions/${TRANSACTION_ID}/pay/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF_TOKEN
        },
        body: JSON.stringify(payload)
    })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                if (data.status === 'completed') {
                    showSaleCompleteModal(data);
                    playSuccessSound();
                } else {
                    // Partial payment
                    showToast(`Partial payment of ${formatCurrency(amount)} received`, 'success');
                    const dueEl = document.getElementById('payment-amount-due');
                    if (dueEl) dueEl.textContent = formatCurrency(parseFloat(data.remaining));

                    const cashInput = document.getElementById('cash-amount');
                    if (cashInput) cashInput.value = '';
                    tenderedAmount = 0;
                    updatePaymentDetails();
                    loadCart(); // Refresh cart UI
                }
            } else {
                showToast(data.error || 'Payment failed', 'error');
            }
        })
        .catch(err => {
            console.error('Payment error:', err);
            showToast('Network error during payment', 'error');
        })
        .finally(() => {
            if (checkoutBtn) checkoutBtn.disabled = false;
        });
}

function showSaleCompleteModal(data) {
    const modalEl = document.getElementById('saleCompleteModal');
    if (!modalEl) {
        alert('Sale Complete! Transaction: ' + (data.transaction_number || ''));
        window.location.reload();
        return;
    }

    const modal = new bootstrap.Modal(modalEl);
    const txnNumEl = document.getElementById('complete-txn-number');
    if (txnNumEl) txnNumEl.textContent = data.transaction_number || '';

    const changeInfo = document.getElementById('change-info');
    const changeAmount = document.getElementById('change-amount');

    if (data.change_due && parseFloat(data.change_due) > 0) {
        if (changeInfo) changeInfo.classList.remove('d-none');
        if (changeAmount) changeAmount.textContent = formatCurrency(parseFloat(data.change_due));
    } else {
        if (changeInfo) changeInfo.classList.add('d-none');
    }

    // Hide payment modal
    const pModalEl = document.getElementById('paymentModal');
    if (pModalEl) {
        const pModal = bootstrap.Modal.getInstance(pModalEl);
        if (pModal) pModal.hide();
    }

    modal.show();

    // Hook up buttons
    const newSaleBtn = document.getElementById('new-sale-btn');
    if (newSaleBtn) {
        newSaleBtn.onclick = function () {
            window.location.href = '/pos/terminal/';
        };
    }

    const printReceiptBtn = document.getElementById('print-receipt-btn');
    if (printReceiptBtn) {
        printReceiptBtn.onclick = function () {
            if (data.receipt_id) {
                window.open(`/pos/receipts/${data.receipt_id}/print/`, '_blank');
            }
        };
    }
}

// Add init call to DOMContentLoaded
document.addEventListener('DOMContentLoaded', initPaymentLogic);
