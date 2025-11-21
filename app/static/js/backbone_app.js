// Mini-ejemplo Backbone para mostrar cómo consumir la API /api/products
// Requiere: jQuery, Underscore y Backbone cargados en la página

$(function() {
    var Product = Backbone.Model.extend({
        // Backbone intentará usar collection.url para creates y /api/products/:id para models con id
    });

    var Products = Backbone.Collection.extend({
        url: '/api/products',
        model: Product
    });

    var ProductView = Backbone.View.extend({
        tagName: 'div',
        className: 'producto backbone-producto',
        template: _.template('<div class="imagenes_producto"><img class="imagen_producto" src="<%- img %>" alt="<%- title %>"></div><h3 class="product-title"><%- title %></h3><p class="product-price">$<%- price %></p><div class="backbone-controls"><button class="delete-btn">Eliminar</button></div>'),
        events: {
            'click .delete-btn': 'onDelete'
        },
        render: function() {
            var data = this.model.toJSON();
            // fallback a placeholder si no hay imagen
            if (!data.img) data.img = '/static/img/Imagenes/placeholder.svg';
            this.$el.html(this.template(data));
            return this;
        },
        onDelete: function() {
            var self = this;
            if (confirm('Eliminar este producto?')) {
                this.model.destroy({
                    wait: true,
                    success: function() {
                        self.remove();
                    },
                    error: function() {
                        alert('No se pudo eliminar el producto.');
                    }
                });
            }
        }
    });

    var AppView = Backbone.View.extend({
        el: '#backbone-products',
        initialize: function() {
            this.collection = new Products();
            this.listenTo(this.collection, 'reset update', this.render);
            this.collection.fetch({reset: true});
        },
        render: function() {
            var self = this;
            this.$el.empty();

            // Formulario simple para crear productos (útil para pruebas/dev)
            var form = $(
                '<div class="backbone-form">' +
                '<input id="bp-title" placeholder="Título" />' +
                '<input id="bp-price" placeholder="Precio" />' +
                '<input id="bp-img" placeholder="URL imagen (/static/...)" />' +
                '<button id="bp-add">Agregar producto</button>' +
                '</div>'
            );
            this.$el.append(form);

            form.on('click', '#bp-add', function(e) {
                e.preventDefault();
                var title = form.find('#bp-title').val().trim();
                var price = parseFloat(form.find('#bp-price').val()) || 0;
                var img = form.find('#bp-img').val().trim() || '/static/img/Imagenes/placeholder.svg';
                if (!title) { alert('Título requerido'); return; }

                self.collection.create({ title: title, price: price, img: img }, {
                    wait: true,
                    success: function() {
                        form.find('#bp-title').val('');
                        form.find('#bp-price').val('');
                        form.find('#bp-img').val('');
                    },
                    error: function() {
                        alert('Error al crear el producto');
                    }
                });
            });

            // Render list
            this.collection.each(function(m) {
                var view = new ProductView({model: m});
                self.$el.append(view.render().el);
            });
        }
    });

    // Inicializa la aplicación Backbone si existe el contenedor
    if ($('#backbone-products').length) {
        new AppView();
    }
});
