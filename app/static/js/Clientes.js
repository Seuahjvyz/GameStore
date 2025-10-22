// Customer Management Functions

function openAddCustomerModal() {
  document.getElementById("customerModal").style.display = "flex"
  document.getElementById("customerModalTitle").textContent = "Agregar Cliente"
  document.getElementById("customerForm").reset()
}

function closeCustomerModal() {
  document.getElementById("customerModal").style.display = "none"
}

function editCustomer(customerId) {
  openAddCustomerModal()
  document.getElementById("customerModalTitle").textContent = "Editar Cliente"
  // Load customer data here
  showNotification("Cargando datos del cliente...", "info")
}

function deleteCustomer(customerId) {
  if (confirm("¿Estás seguro de que deseas eliminar este cliente?")) {
    showNotification("Cliente eliminado exitosamente", "success")
    // Delete logic here
  }
}

function viewCustomerHistory(customerId) {
  showNotification("Abriendo historial del cliente...", "info")
  // Navigate to customer history page
}

function showNotification(message, type) {
  console.log(`Notification: ${message} (Type: ${type})`)
}

document.getElementById("customerForm")?.addEventListener("submit", (e) => {
  e.preventDefault()
  showNotification("Cliente guardado exitosamente", "success")
  closeCustomerModal()
})
