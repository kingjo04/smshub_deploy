// Event Listeners
document.getElementById('createOrderBtn').addEventListener('click', createOrder);
document.getElementById('refreshBtn').addEventListener('click', updateStatuses);

// Fungsi utama
async function createOrder() {
    try {
        const btn = document.getElementById('createOrderBtn');
        btn.innerHTML = '⏳ Membuat...';
        btn.disabled = true;

        const response = await fetch('/api/create_order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ service: 'go' })
        });
        
        const result = await response.json();
        if (!response.ok) throw result.error || 'Gagal membuat order';
        
        alert(`✅ Order ${result.order_id} berhasil dibuat!`);
        fetchOrders();
        
    } catch (error) {
        alert(`❌ Error: ${error}`);
    } finally {
        btn.innerHTML = '🆕 Buat Order Baru';
        btn.disabled = false;
    }
}

// Fungsi-fungsi lain tetap sama seperti sebelumnya
// ... [rest of the functions from previous script.js]

// Initialize
fetchOrders();
startAutoRefresh();