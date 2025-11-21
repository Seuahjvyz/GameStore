// Shared site actions: cart, favorites, search, and checkout handlers.
(function(){
    function getCsrf(){
        var m = document.querySelector('meta[name="csrf-token"]');
        return m ? m.content : '';
    }

    document.addEventListener('DOMContentLoaded', function(){
        var csrf = getCsrf();
        var cartCountEl = document.getElementById('cart-count');
        function setCartCount(n){ if(cartCountEl) cartCountEl.textContent = n; }

        // Simple toast helper
        function ensureToastContainer(){
            var c = document.getElementById('toast-container');
            if(c) return c;
            c = document.createElement('div');
            c.id = 'toast-container';
            c.style.position = 'fixed';
            c.style.right = '16px';
            c.style.bottom = '16px';
            c.style.zIndex = 9999;
            document.body.appendChild(c);
            return c;
        }

        function showToast(msg, timeout){
            timeout = timeout || 3000;
            var c = ensureToastContainer();
            var el = document.createElement('div');
            el.textContent = msg;
            el.style.background = 'rgba(0,0,0,0.85)';
            el.style.color = 'white';
            el.style.padding = '10px 14px';
            el.style.marginTop = '8px';
            el.style.borderRadius = '6px';
            el.style.boxShadow = '0 2px 8px rgba(0,0,0,0.3)';
            el.style.fontSize = '14px';
            c.appendChild(el);
            setTimeout(function(){ el.style.opacity = '0'; setTimeout(function(){ c.removeChild(el); }, 400); }, timeout);
        }

        // Add to cart buttons
        document.querySelectorAll('.btn_carrito').forEach(function(b){
            b.addEventListener('click', function(){
                var pid = this.getAttribute('data-pid');
                if(!pid) return;
                fetch('/cart/add', {
                    method: 'POST',
                    headers: {'Content-Type':'application/json','X-CSRF-Token': csrf},
                    body: JSON.stringify({pid: pid, qty: 1, csrf_token: csrf})
                }).then(function(r){ return r.json(); }).then(function(j){
                    if(j && j.ok){
                        setCartCount(j.total_items);
                        b.classList.add('added');
                        setTimeout(function(){ b.classList.remove('added'); }, 800);
                        showToast('Añadido al carrito');
                    } else if(j && j.error){
                        showToast('No se pudo añadir al carrito: ' + j.error);
                    } else {
                        showToast('No se pudo añadir al carrito');
                    }
                }).catch(function(){ showToast('Error agregando al carrito'); });
            });
        });

        // Favorites toggle
        document.querySelectorAll('.btn_fav').forEach(function(b){
            b.addEventListener('click', function(){
                var pid = this.getAttribute('data-pid');
                var self = this;
                if(!pid) return;
                fetch('/favorites/toggle', {
                    method: 'POST',
                    headers: {'Content-Type':'application/json','X-CSRF-Token': csrf},
                    body: JSON.stringify({pid: pid, csrf_token: csrf})
                }).then(function(r){ return r.json(); }).then(function(j){
                    if(j && j.ok){
                        if(j.action === 'added'){
                            self.classList.add('fav-active');
                            showToast('Añadido a favoritos');
                        } else {
                            self.classList.remove('fav-active');
                            showToast('Eliminado de favoritos');
                        }
                    } else if(j && j.error){
                        showToast('No se pudo actualizar favoritos: ' + j.error);
                    } else {
                        showToast('No se pudo actualizar favoritos');
                    }
                }).catch(function(){ showToast('Error actualizando favoritos'); });
            });
        });

        // Search box
        var buscarBtn = document.getElementById('buscar-btn');
        var buscarInput = document.getElementById('buscar-input');
        if(buscarBtn && buscarInput){
            buscarBtn.addEventListener('click', function(){
                var q = buscarInput.value || '';
                window.location = '/?q=' + encodeURIComponent(q);
            });
        }

        // Cart remove buttons (present on Carrito.html)
        document.querySelectorAll('.btn_eliminar').forEach(function(b){
            b.addEventListener('click', function(){
                var pid = this.getAttribute('data-pid');
                if(!pid) return;
                var btn = this;
                fetch('/cart/remove', {
                    method: 'POST',
                    headers: {'Content-Type':'application/json','X-CSRF-Token': csrf},
                    body: JSON.stringify({pid: pid, csrf_token: csrf})
                }).then(function(r){ return r.json(); }).then(function(j){
                    if(j && j.ok){
                        // remove product node from DOM
                        var prod = btn.closest('.producto');
                        if(prod){
                            var itemSubtotal = parseFloat(prod.getAttribute('data-subtotal') || '0');
                            prod.parentNode.removeChild(prod);
                            // update subtotal and total
                            var subtotalEl = document.getElementById('subtotal');
                            var totalEl = document.getElementById('total');
                            function parseMoney(el){ if(!el) return 0; return parseFloat((el.textContent||'').replace(/[^0-9.,-]+/g,'').replace(',','.')) || 0; }
                            function formatMoney(v){ return '$' + v.toFixed(2); }
                            var curSub = parseMoney(subtotalEl);
                            var curTotal = parseMoney(totalEl);
                            var newSub = Math.max(0, curSub - itemSubtotal);
                            var newTotal = Math.max(0, curTotal - itemSubtotal);
                            if(subtotalEl) subtotalEl.textContent = formatMoney(newSub);
                            if(totalEl) totalEl.textContent = formatMoney(newTotal);
                        }
                        setCartCount(j.total_items);
                        showToast('Producto eliminado');
                        // if no products left, optionally show message
                        if(document.querySelectorAll('.producto').length === 0){
                            var productsSection = document.querySelector('.productos');
                            if(productsSection){ productsSection.innerHTML = '<p>No hay productos en el carrito.</p>'; }
                        }
                    } else if(j && j.error){
                        showToast('No se pudo eliminar el producto: ' + j.error);
                    } else {
                        showToast('No se pudo eliminar el producto');
                    }
                }).catch(function(){ showToast('Error eliminando'); });
            });
        });

        // Checkout handler: if we're on the Cart page, go to payment screen; if on payment screen, perform the POST.
        var checkout = document.getElementById('checkoutBtn');
        if(checkout){
            checkout.addEventListener('click', function(e){
                e.preventDefault();
                // If this page contains a payment form (user on /pagar), proceed to submit to /checkout.
                var paymentFormPresent = document.querySelector('.datos_bancarios_2') || document.querySelector('.payment-container') || document.getElementById('titular_tarjeta');
                if(!paymentFormPresent){
                    // redirect to payment page where user can enter card details
                    window.location = '/pagar';
                    return;
                }
                // Otherwise, perform the checkout POST (AJAX with fallback)
                // disable button to avoid double submits
                checkout.disabled = true;
                checkout.classList.add('loading');
                showToast('Procesando pago...');
                fetch('/checkout', {
                    method: 'POST',
                    headers: {'Content-Type':'application/json','X-CSRF-Token': csrf},
                    body: JSON.stringify({csrf_token: csrf})
                }).then(function(r){
                    // Try to parse JSON, but handle non-JSON gracefully
                    return r.text().then(function(text){
                        try{
                            return JSON.parse(text);
                        }catch(err){
                            return {__raw_text: text, status: r.status};
                        }
                    });
                }).then(function(j){
                    checkout.disabled = false;
                    checkout.classList.remove('loading');
                    if(j && j.ok){
                        showToast('Pedido creado: ' + j.order_id);
                        setTimeout(function(){ window.location = '/'; }, 800);
                        return;
                    }
                    if(j && j.error){
                        showToast('Error: ' + j.error);
                        return;
                    }
                    // If server returned HTML (e.g., rendered page) or non-json, fallback to form submit
                    if(j && j.__raw_text){
                        showToast('Respuesta recibida — intentando completar pago...');
                        // create and submit a form as a fallback
                        var f = document.createElement('form');
                        f.method = 'POST'; f.action = '/checkout';
                        var inp = document.createElement('input'); inp.type = 'hidden'; inp.name = 'csrf_token'; inp.value = csrf; f.appendChild(inp);
                        document.body.appendChild(f);
                        f.submit();
                        return;
                    }
                    showToast('Error creando el pedido');
                }).catch(function(err){
                    // network or other error — try form fallback
                    checkout.disabled = false;
                    checkout.classList.remove('loading');
                    showToast('Error en checkout — intentando por formulario');
                    var f = document.createElement('form');
                    f.method = 'POST'; f.action = '/checkout';
                    var inp = document.createElement('input'); inp.type = 'hidden'; inp.name = 'csrf_token'; inp.value = csrf; f.appendChild(inp);
                    document.body.appendChild(f);
                    f.submit();
                });
            });
        }
    });
})();

// Admin helpers: delete confirmation modal and price-validation for forms
(function(){
    document.addEventListener('DOMContentLoaded', function(){
        // Delete modal handling (inventory admin)
        var modal = document.getElementById('deleteModal');
        if(modal){
            var closeBtn = modal.querySelector('.modal-close');
            var cancelBtn = document.getElementById('cancelDelete');
            var confirmBtn = document.getElementById('confirmDelete');
            var pendingPid = null;
            function openModal(pid){ pendingPid = pid; modal.style.display = 'block'; }
            function closeModal(){ pendingPid = null; modal.style.display = 'none'; }
            document.querySelectorAll('.delete-trigger').forEach(function(btn){
                btn.addEventListener('click', function(e){
                    var pid = this.getAttribute('data-pid');
                    openModal(pid);
                });
            });
            if(closeBtn) closeBtn.addEventListener('click', closeModal);
            if(cancelBtn) cancelBtn.addEventListener('click', function(e){ e.preventDefault(); closeModal(); });
            if(confirmBtn) confirmBtn.addEventListener('click', function(e){
                if(!pendingPid) return closeModal();
                var form = document.querySelector('.product-delete-form[data-pid="'+pendingPid+'"]');
                if(form) form.submit();
                closeModal();
            });
            window.addEventListener('click', function(e){ if(e.target === modal) closeModal(); });
        }

        // Price validation for forms (add/edit product)
        document.querySelectorAll('form').forEach(function(form){
            if(!form.querySelector('[name="price"]')) return;
            form.addEventListener('submit', function(e){
                var priceEl = form.querySelector('[name="price"]');
                if(!priceEl) return;
                var price = (priceEl.value || '').trim();
                var v = parseFloat(price);
                if(isNaN(v) || !isFinite(v) || v < 0){
                    e.preventDefault();
                    alert('Por favor ingresa un precio válido (número mayor o igual a 0).');
                    return false;
                }
            });
        });
    });
})();
