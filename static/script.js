// Event Listeners
document.getElementById('createOrderBtn').addEventListener('click', createOrder);
document.getElementById('refreshBtn').addEventListener('click', updateStatuses);

// Fungsi inisialisasi dropdown
async function populateDropdowns() {
    try {
        const [servicesResponse, countriesResponse] = await Promise.all([
            fetch('/api/all_services'),
            fetch('/api/all_countries')
        ]);
        const services = await servicesResponse.json();
        const countries = await countriesResponse.json();

        const serviceSelect = document.getElementById('serviceSelect');
        const countrySelect = document.getElementById('countrySelect');

        if (services.success) {
            services.services.forEach(service => {
                const option = document.createElement('option');
                option.value = service;
                option.textContent = SERVICES[service] || service;
                serviceSelect.appendChild(option);
            });
        }
        if (countries.success) {
            countries.countries.forEach(country => {
                const option = document.createElement('option');
                option.value = country;
                option.textContent = COUNTRIES[country] || country;
                countrySelect.appendChild(option);
            });
        }
    } catch (error) {
        showNotification(`❌ Error memuat dropdown: ${error}`, 'error');
    }
}

// Fungsi utama
async function createOrder() {
    try {
        const btn = document.getElementById('createOrderBtn');
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
        showNotification(`❌ Error: ${error}`, 'error');
    } finally {
        const btn = document.getElementById('createOrderBtn');
        btn.innerHTML = '🆕 Buat Order Baru';
        btn.disabled = false;
    }
}

// Fungsi update status real-time
function updateStatuses() {
    fetch('/api/orders')
        .then(response => response.json())
        .then(data => {
            updateOrderTable(data.active_orders, 'activeOrders');
            updateOrderTable(data.history_orders, 'historyOrders');
            startRealtimeTimer();
        })
        .catch(error => showNotification(`❌ Error: ${error}`, 'error'));
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
    const tableBody = document.getElementById(tableId).getElementsByTagName('tbody')[0];
    tableBody.innerHTML = '';
    orders.forEach(order => {
        const row = tableBody.insertRow();
        row.innerHTML = `
            <td>${order.number}</td>
            <td>${order.service}</td>
            <td>${order.country}</td>
            <td>${order.status}</td>
            <td id="timer-${order.id}">${calculateRemainingTime(order.expires_at)}</td>
            <td>${new Date(order.created_at).toLocaleString()}</td>
            ${tableId === 'historyOrders' ? `<td>${order.sms_code || '-'}</td>` : '<td><button onclick="cancelOrder(\'' + order.id + '\')">Batal</button></td>'}
        `;
    });
}

// Fungsi hitung sisa waktu
function calculateRemainingTime(expiresAt) {
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
                    timer.textContent = calculateRemainingTime(order.expires_at);
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
populateDropdowns();
fetchOrders();
startAutoRefresh();
