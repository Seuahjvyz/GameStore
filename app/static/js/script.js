// ============================================
// GAME STORE WEB - JAVASCRIPT COMPLETO
// ============================================

// ============================================
// 1. BÚSQUEDA Y FILTRADO
// ============================================

// Búsqueda en tiempo real
function setupSearch() {
  const searchInputs = document.querySelectorAll(".search-input")

  searchInputs.forEach((input) => {
    input.addEventListener("input", (e) => {
      const searchTerm = e.target.value.toLowerCase()
      filterProducts(searchTerm)
      filterTableRows(searchTerm)
    })
  })
}

// Filtrar productos
function filterProducts(searchTerm) {
  const productCards = document.querySelectorAll(".product-card")

  productCards.forEach((card) => {
    const title = card.querySelector(".product-title")?.textContent.toLowerCase() || ""
    const price = card.querySelector(".product-price")?.textContent.toLowerCase() || ""

    if (title.includes(searchTerm) || price.includes(searchTerm)) {
      card.style.display = "block"
    } else {
      card.style.display = "none"
    }
  })
}

// Filtrar filas de tabla
function filterTableRows(searchTerm) {
  const tableRows = document.querySelectorAll("tbody tr")

  tableRows.forEach((row) => {
    const text = row.textContent.toLowerCase()

    if (text.includes(searchTerm)) {
      row.style.display = ""
    } else {
      row.style.display = "none"
    }
  })
}

// ============================================
// 2. ORDENAMIENTO
// ============================================

// Ordenar productos por precio
function sortProductsByPrice(ascending = true) {
  const grid = document.querySelector(".products-grid")
  if (!grid) return

  const products = Array.from(grid.querySelectorAll(".product-card"))

  products.sort((a, b) => {
    const priceA = Number.parseFloat(a.querySelector(".product-price").textContent.replace("$", ""))
    const priceB = Number.parseFloat(b.querySelector(".product-price").textContent.replace("$", ""))

    return ascending ? priceA - priceB : priceB - priceA
  })

  products.forEach((product) => grid.appendChild(product))
}

// Ordenar productos por nombre
function sortProductsByName(ascending = true) {
  const grid = document.querySelector(".products-grid")
  if (!grid) return

  const products = Array.from(grid.querySelectorAll(".product-card"))

  products.sort((a, b) => {
    const nameA = a.querySelector(".product-title").textContent.toLowerCase()
    const nameB = b.querySelector(".product-title").textContent.toLowerCase()

    if (ascending) {
      return nameA.localeCompare(nameB)
    } else {
      return nameB.localeCompare(nameA)
    }
  })

  products.forEach((product) => grid.appendChild(product))
}

// Ordenar tabla por columna
function sortTable(columnIndex, ascending = true) {
  const table = document.querySelector("table")
  if (!table) return

  const tbody = table.querySelector("tbody")
  const rows = Array.from(tbody.querySelectorAll("tr"))

  rows.sort((a, b) => {
    const cellA = a.cells[columnIndex].textContent.trim()
    const cellB = b.cells[columnIndex].textContent.trim()

    // Intentar comparar como números
    const numA = Number.parseFloat(cellA.replace(/[^0-9.-]/g, ""))
    const numB = Number.parseFloat(cellB.replace(/[^0-9.-]/g, ""))

    if (!isNaN(numA) && !isNaN(numB)) {
      return ascending ? numA - numB : numB - numA
    }

    // Comparar como texto
    return ascending ? cellA.localeCompare(cellB) : cellB.localeCompare(cellA)
  })

  rows.forEach((row) => tbody.appendChild(row))
}

// ============================================
// 3. NOTIFICACIONES
// ============================================

function showNotification(message, type = "success") {
  // Remover notificación existente
  const existingNotification = document.querySelector(".notification")
  if (existingNotification) {
    existingNotification.remove()
  }

  // Crear nueva notificación
  const notification = document.createElement("div")
  notification.className = `notification notification-${type}`
  notification.textContent = message

  document.body.appendChild(notification)

  // Mostrar con animación
  setTimeout(() => {
    notification.classList.add("show")
  }, 10)

  // Ocultar después de 3 segundos
  setTimeout(() => {
    notification.classList.remove("show")
    setTimeout(() => {
      notification.remove()
    }, 300)
  }, 3000)
}

// ============================================
// 4. GESTIÓN DE CARRITO
// ============================================

let cart = JSON.parse(localStorage.getItem("cart")) || []

function addToCart(productId, productName, price) {
  const existingItem = cart.find((item) => item.id === productId)

  if (existingItem) {
    existingItem.quantity += 1
  } else {
    cart.push({
      id: productId,
      name: productName,
      price: price,
      quantity: 1,
    })
  }

  saveCart()
  showNotification(`${productName} agregado al carrito`, "success")
  updateCartCount()
}

function removeFromCart(productId) {
  cart = cart.filter((item) => item.id !== productId)
  saveCart()
  showNotification("Producto eliminado del carrito", "success")
  updateCartCount()
}

function updateCartQuantity(productId, quantity) {
  const item = cart.find((item) => item.id === productId)
  if (item) {
    item.quantity = quantity
    if (item.quantity <= 0) {
      removeFromCart(productId)
    } else {
      saveCart()
      updateCartCount()
    }
  }
}

function clearCart() {
  cart = []
  saveCart()
  showNotification("Carrito vaciado", "success")
  updateCartCount()
}

function saveCart() {
  localStorage.setItem("cart", JSON.stringify(cart))
}

function getCartTotal() {
  return cart.reduce((total, item) => total + item.price * item.quantity, 0)
}

function updateCartCount() {
  const cartCount = cart.reduce((total, item) => total + item.quantity, 0)
  const cartBadges = document.querySelectorAll(".cart-count")
  cartBadges.forEach((badge) => {
    badge.textContent = cartCount
  })
}

// ============================================
// 5. VALIDACIÓN DE FORMULARIOS
// ============================================

function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(email)
}

function validatePhone(phone) {
  const re = /^[\d\s\-+$$$$]+$/
  return re.test(phone) && phone.replace(/\D/g, "").length >= 10
}

function validateForm(formElement) {
  const inputs = formElement.querySelectorAll("input[required], textarea[required], select[required]")
  let isValid = true

  inputs.forEach((input) => {
    if (!input.value.trim()) {
      isValid = false
      input.style.borderColor = "#ef4444"
    } else {
      input.style.borderColor = "#2a2a2a"

      // Validaciones específicas
      if (input.type === "email" && !validateEmail(input.value)) {
        isValid = false
        input.style.borderColor = "#ef4444"
      }

      if (input.type === "tel" && !validatePhone(input.value)) {
        isValid = false
        input.style.borderColor = "#ef4444"
      }
    }
  })

  return isValid
}

// ============================================
// 6. GESTIÓN DE PRODUCTOS (CRUD)
// ============================================

let products = JSON.parse(localStorage.getItem("products")) || []

function addProduct(product) {
  products.push({
    id: Date.now(),
    ...product,
    createdAt: new Date().toISOString(),
  })
  saveProducts()
  showNotification("Producto agregado exitosamente", "success")
}

function updateProduct(productId, updatedData) {
  const index = products.findIndex((p) => p.id === productId)
  if (index !== -1) {
    products[index] = { ...products[index], ...updatedData }
    saveProducts()
    showNotification("Producto actualizado exitosamente", "success")
  }
}

function deleteProduct(productId) {
  products = products.filter((p) => p.id !== productId)
  saveProducts()
  showNotification("Producto eliminado exitosamente", "success")
}

function saveProducts() {
  localStorage.setItem("products", JSON.stringify(products))
}

function getProductById(productId) {
  return products.find((p) => p.id === productId)
}

// ============================================
// 7. GESTIÓN DE USUARIOS
// ============================================

let users = JSON.parse(localStorage.getItem("users")) || []

function addUser(user) {
  users.push({
    id: Date.now(),
    ...user,
    createdAt: new Date().toISOString(),
  })
  saveUsers()
  showNotification("Usuario agregado exitosamente", "success")
}

function updateUser(userId, updatedData) {
  const index = users.findIndex((u) => u.id === userId)
  if (index !== -1) {
    users[index] = { ...users[index], ...updatedData }
    saveUsers()
    showNotification("Usuario actualizado exitosamente", "success")
  }
}

function deleteUser(userId) {
  users = users.filter((u) => u.id !== userId)
  saveUsers()
  showNotification("Usuario eliminado exitosamente", "success")
}

function saveUsers() {
  localStorage.setItem("users", JSON.stringify(users))
}

// ============================================
// 8. GESTIÓN DE PEDIDOS
// ============================================

const orders = JSON.parse(localStorage.getItem("orders")) || []

function createOrder(orderData) {
  const order = {
    id: Date.now(),
    orderNumber: `ORD-${String(orders.length + 1).padStart(3, "0")}`,
    ...orderData,
    status: "pending",
    createdAt: new Date().toISOString(),
  }

  orders.push(order)
  saveOrders()
  showNotification("Pedido creado exitosamente", "success")
  return order
}

function updateOrderStatus(orderId, status) {
  const order = orders.find((o) => o.id === orderId)
  if (order) {
    order.status = status
    order.updatedAt = new Date().toISOString()
    saveOrders()
    showNotification("Estado del pedido actualizado", "success")
  }
}

function saveOrders() {
  localStorage.setItem("orders", JSON.stringify(orders))
}

// ============================================
// 9. EXPORTACIÓN DE DATOS
// ============================================

function exportToCSV(data, filename) {
  if (!data || data.length === 0) {
    showNotification("No hay datos para exportar", "warning")
    return
  }

  const headers = Object.keys(data[0])
  const csvContent = [
    headers.join(","),
    ...data.map((row) => headers.map((header) => JSON.stringify(row[header] || "")).join(",")),
  ].join("\n")

  downloadFile(csvContent, filename, "text/csv")
  showNotification("Datos exportados exitosamente", "success")
}

function exportToJSON(data, filename) {
  const jsonContent = JSON.stringify(data, null, 2)
  downloadFile(jsonContent, filename, "application/json")
  showNotification("Datos exportados exitosamente", "success")
}

function downloadFile(content, filename, mimeType) {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

// ============================================
// 10. IMPRESIÓN
// ============================================

function printReport() {
  window.print()
}

function printElement(elementId) {
  const element = document.getElementById(elementId)
  if (!element) return

  const printWindow = window.open("", "", "height=600,width=800")
  printWindow.document.write("<html><head><title>Imprimir</title>")
  printWindow.document.write('<link rel="stylesheet" href="styles/game-store.css">')
  printWindow.document.write("</head><body>")
  printWindow.document.write(element.innerHTML)
  printWindow.document.write("</body></html>")
  printWindow.document.close()
  printWindow.print()
}

// ============================================
// 11. ESTADÍSTICAS
// ============================================

function calculateStats() {
  const totalSales = orders.reduce((sum, order) => sum + (order.total || 0), 0)
  const totalOrders = orders.length
  const averageOrderValue = totalOrders > 0 ? totalSales / totalOrders : 0
  const totalProducts = products.length
  const totalUsers = users.length

  return {
    totalSales,
    totalOrders,
    averageOrderValue,
    totalProducts,
    totalUsers,
  }
}

function updateDashboardStats() {
  const stats = calculateStats()

  const statElements = {
    totalSales: document.querySelector('[data-stat="total-sales"]'),
    totalOrders: document.querySelector('[data-stat="total-orders"]'),
    averageOrder: document.querySelector('[data-stat="average-order"]'),
    totalProducts: document.querySelector('[data-stat="total-products"]'),
    totalUsers: document.querySelector('[data-stat="total-users"]'),
  }

  if (statElements.totalSales) {
    statElements.totalSales.textContent = `$${stats.totalSales.toFixed(2)}`
  }
  if (statElements.totalOrders) {
    statElements.totalOrders.textContent = stats.totalOrders
  }
  if (statElements.averageOrder) {
    statElements.averageOrder.textContent = `$${stats.averageOrderValue.toFixed(2)}`
  }
  if (statElements.totalProducts) {
    statElements.totalProducts.textContent = stats.totalProducts
  }
  if (statElements.totalUsers) {
    statElements.totalUsers.textContent = stats.totalUsers
  }
}

// ============================================
// 12. SIDEBAR MÓVIL
// ============================================

function toggleSidebar() {
  const sidebar = document.querySelector(".sidebar")
  if (sidebar) {
    sidebar.classList.toggle("open")
  }
}

// ============================================
// 13. MANEJO DE EVENTOS DE BOTONES
// ============================================

function setupActionButtons() {
  // Botones de eliminar
  document.querySelectorAll(".btn-icon.delete").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      if (confirm("¿Estás seguro de que deseas eliminar este elemento?")) {
        const row = e.target.closest("tr")
        if (row) {
          row.remove()
          showNotification("Elemento eliminado", "success")
        }
      }
    })
  })

  // Botones de editar
  document.querySelectorAll('.btn-icon[title="Editar"]').forEach((btn) => {
    btn.addEventListener("click", () => {
      showNotification("Función de edición en desarrollo", "warning")
    })
  })
}

// ============================================
// 14. INICIALIZACIÓN
// ============================================

document.addEventListener("DOMContentLoaded", () => {
  // Configurar búsqueda
  setupSearch()

  // Configurar botones de acción
  setupActionButtons()

  // Actualizar contador del carrito
  updateCartCount()

  // Actualizar estadísticas del dashboard
  updateDashboardStats()

  // Configurar formularios
  document.querySelectorAll("form").forEach((form) => {
    form.addEventListener("submit", (e) => {
      e.preventDefault()

      if (validateForm(form)) {
        showNotification("Formulario enviado exitosamente", "success")
        form.reset()
      } else {
        showNotification("Por favor completa todos los campos requeridos", "error")
      }
    })
  })

  // Configurar botones de búsqueda
  document.querySelectorAll(".search-button").forEach((btn) => {
    btn.addEventListener("click", () => {
      const input = btn.previousElementSibling
      if (input) {
        const searchTerm = input.value.toLowerCase()
        filterProducts(searchTerm)
        filterTableRows(searchTerm)
      }
    })
  })

  // Configurar clicks en tarjetas de productos
  document.querySelectorAll(".product-card").forEach((card) => {
    card.addEventListener("click", () => {
      const title = card.querySelector(".product-title")?.textContent
      const price = card.querySelector(".product-price")?.textContent
      showNotification(`Producto seleccionado: ${title} - ${price}`, "success")
    })
  })

  console.log("Game Store Web - Sistema inicializado correctamente")
})

// ============================================
// 15. UTILIDADES ADICIONALES
// ============================================

// Formatear moneda
function formatCurrency(amount) {
  return new Intl.NumberFormat("es-ES", {
    style: "currency",
    currency: "USD",
  }).format(amount)
}

// Formatear fecha
function formatDate(date) {
  return new Intl.DateTimeFormat("es-ES", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(date))
}

// Debounce para optimizar búsquedas
function debounce(func, wait) {
  let timeout
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

