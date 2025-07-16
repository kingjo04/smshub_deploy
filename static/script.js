// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    const createOrderBtn = document.getElementById('createOrderBtn');
    const refreshBtn = document.getElementById('refreshBtn');
    if (createOrderBtn) createOrderBtn.addEventListener('click', createOrder);
    if (refreshBtn) refreshBtn.addEventListener('click', updateStatuses);
    console.log('DOM Loaded, buttons:', { createOrderBtn, refreshBtn });
});

// Fungsi utama
async function createOrder() {
    const btn = document.getElementById('createOrderBtn');
    if (!btn) {
        showNotification('❌ Error: Tombol Buat Order tidak ditemukan', 'error');
        console.error('Button not found:', btn);
        return;
    }

    try {
        btn.innerHTML = '⏳ Membuat...';
        btn.disabled = true;

        const service = document.getElementById('serviceSelect').value;
        const country = document.getElementById('countrySelect').value;
        if (!service || !country) {
            throw new Error('Pilih layanan dan negara terlebih dahulu');
        }

        const response = await fetch('/api/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ service, country })
        });
        
        const result = await response.json();
        if (!response.ok) throw result.error || 'Gagal membuat order';
        
        showNotification(`✅ Order ${result.order.id} berhasil dibuat!`, 'success');
        fetchOrders();
        
    } catch (error) {
        showNotification(`❌ Error: ${error.message || error}`, 'error');
        console.error('Create order error:', error);
    } finally {
        if (btn) {
            btn.innerHTML = '🆕 Buat Order Baru';
            btn.disabled = false;
        }
    }
}

// Fungsi update status real-time
function updateStatuses() {
    const activeTable = document.getElementById('activeOrders');
    const historyTable = document.getElementById('historyOrders');
    console.log('Checking tables:', { activeTable, historyTable });
    if (!activeTable || !historyTable) {
        showNotification('❌ Error: Tabel order tidak ditemukan', 'error');
        console.error('Tables not found:', { activeTable, historyTable });
        return;
    }

    fetch('/api/orders')
        .then(response => response.json())
        .then(data => {
            updateOrderTable(data.active_orders, 'activeOrders');
            updateOrderTable(data.history_orders, 'historyOrders');
            startRealtimeTimer();
        })
        .catch(error => {
            showNotification(`❌ Error: ${error}`, 'error');
            console.error('Fetch orders error:', error);
        });
}

// Fungsi tampilkan notifikasi
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

// Fungsi update tabel
function updateOrderTable(orders, tableId) {
    const tableBody = document.getElementById(tableId)?.getElementsByTagName('tbody')[0];
    if (!tableBody) {
        showNotification(`❌ Error: Bagian tabel ${tableId} tidak ditemukan`, 'error');
        console.error(`Table body ${tableId} not found:`, tableBody);
        return;
    }
    tableBody.innerHTML = '';
    orders.forEach(order => {
        const row = tableBody.insertRow();
        row.innerHTML = `
            <td>${order.number || '-'}</td>
            <td>${order.service || '-'}</td>
            <td>${order.country || '-'}</td>
            <td>${order.status || '-'}</td>
            <td id="timer-${order.id}">${calculateRemainingTime(order.expires_at) || '-'}</td>
            <td>${new Date(order.created_at).toLocaleString() || '-'}</td>
            ${tableId === 'historyOrders' ? `<td>${order.sms_code || '-'}</td>` : '<td><button onclick="cancelOrder(\'' + order.id + '\')">Batal</button></td>'}
        `;
    });
}

// Fungsi hitung sisa waktu
function calculateRemainingTime(expiresAt) {
    if (!expiresAt) return 'Waktu Tidak Tersedia';
    const now = new Date();
    const expires = new Date(expiresAt);
    const diff = expires - now;
    if (diff <= 0) return 'Waktu Habis';
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);
    return `${days}d ${hours}h ${minutes}m ${seconds}s`;
}

// Fungsi real-time timer
function startRealtimeTimer() {
    const timers = document.querySelectorAll('[id^="timer-"]');
    timers.forEach(timer => {
        const orderId = timer.id.split('timer-')[1];
        setInterval(() => {
            fetch(`/api/order/${orderId}`)
                .then(response => response.json())
                .then(order => {
                    if (timer) timer.textContent = calculateRemainingTime(order.expires_at);
                })
                .catch(() => {
                    if (timer) timer.textContent = 'Error';
                });
        }, 1000); // Update tiap 1 detik
    });
}

// Fungsi cancel order
function cancelOrder(orderId) {
    fetch(`/api/cancel/${orderId}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('✅ Order dibatalkan!', 'success');
                fetchOrders();
            } else {
                showNotification('❌ Gagal membatalkan order', 'error');
            }
        });
}

// Fungsi ambil order
function fetchOrders() {
    updateStatuses();
}

// Fungsi auto refresh
function startAutoRefresh() {
    setInterval(fetchOrders, 30000); // Refresh tiap 30 detik
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    fetchOrders();
    startAutoRefresh();
});
