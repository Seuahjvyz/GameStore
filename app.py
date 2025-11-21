from flask import Flask, render_template, send_from_directory, jsonify, request, abort, redirect, url_for, session, flash, get_flashed_messages
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy.exc import OperationalError, IntegrityError

# Configuración de Flask con carpetas existentes
app = Flask(__name__, template_folder=os.path.join('app', 'templates'), static_folder=os.path.join('app', 'static'))
app.secret_key = os.environ.get('FLASK_SECRET', 'dev-secret')

# Base de datos: por defecto SQLite en la raíz del proyecto, pero permite
# sobrescribir con una URL de base de datos (p. ej. Postgres) mediante
# la variable de entorno DATABASE_URL.
db_path = os.path.join(os.path.dirname(__file__), 'gamestore.db')
default_sqlite = f'sqlite:///{db_path}'
DATABASE_URL = os.environ.get('DATABASE_URL') or default_sqlite
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Simple CSRF helpers (no external deps)
import secrets


@app.context_processor
def inject_csrf_token():
    token = session.get('csrf_token')
    if not token:
        token = secrets.token_urlsafe(16)
        session['csrf_token'] = token
    return {'csrf_token': token}


def validate_csrf(form_token):
    tok = session.get('csrf_token')
    if not tok or not form_token or tok != form_token:
        return False
    # Do not remove the token here — keep it persistent for multiple AJAX calls on the same page.
    # If rotation is desired, implement a rotate function and update clients accordingly.
    return True


def get_request_csrf_token():
    """Extract CSRF token from header, form or JSON body for AJAX calls."""
    token = None
    token = request.headers.get('X-CSRF-Token')
    if not token:
        token = (request.form.get('csrf_token') if request.form else None)
    if not token:
        j = None
        try:
            j = request.get_json(silent=True) or {}
        except Exception:
            j = {}
        token = token or j.get('csrf_token')
    return token


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    img = db.Column(db.String(400), nullable=True)
    # binary image stored in DB (optional)
    image_data = db.Column(db.LargeBinary, nullable=True)
    image_mime = db.Column(db.String(120), nullable=True)
    # category (simple string for now)
    category = db.Column(db.String(120), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'price': self.price,
            'img': self.img,
            'image_url': url_for('product_image', pid=self.id) if self.image_data else (self.img or None)
        }


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Additional models for the project: categories, product_images, orders, order_items, payments
class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)


class ProductImage(db.Model):
    __tablename__ = 'product_images'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'))
    url = db.Column(db.String(400), nullable=False)


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    total = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    # relationship for convenience
    order_items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan', lazy='select')


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='SET NULL'))
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, default=0.0)
    # convenience relation to product
    product = db.relationship('Product', backref='order_items', lazy='joined')


class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='SET NULL'))
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(80))
    status = db.Column(db.String(50), default='pending')


def init_db_and_seed():
    # Asegura que las tablas existan y agrega algunos productos de ejemplo si la tabla está vacía
    db.create_all()
    try:
        count = Product.query.count()
    except Exception:
        count = 0

    if count == 0:
        sample = [
            Product(title='XBOX SERIES X 2TB', price=17000, img='/static/img/Imagenes/series x especial.png'),
            Product(title='ZOMBIES GAME', price=450, img='/static/img/Imagenes/gta6.png'),
            Product(title='AUDÍFONOS GAMER', price=760, img='/static/img/Imagenes/Audifonos_Gamer.jpg')
        ]
        db.session.add_all(sample)
        db.session.commit()
    # Ensure there's at least one user (development convenience). Create an admin if no users exist.
    try:
        ucount = User.query.count()
    except Exception:
        ucount = 0
    if ucount == 0:
        admin = User(username='admin')
        admin.set_password('admin')
        admin.is_admin = True
        db.session.add(admin)
        db.session.commit()


def fix_product_images_on_disk():
    """Ajusta rutas de imagen de productos que apuntan a archivos inexistentes.
    Heurística simple: si el nombre contiene 'zombie' se mapeará a 'gta6.png',
    en caso contrario se asignará el placeholder.
    """
    changed = 0
    for p in Product.query.all():
        img = p.img or ''
        if not img:
            p.img = '/static/img/Imagenes/placeholder.svg'
            changed += 1
            continue
        # convertir ruta web a ruta de fichero
        if img.startswith('/static/'):
            rel = img[len('/static/'):]
        elif img.startswith('static/'):
            rel = img[len('static/'):]
        else:
            rel = img
        filesystem_path = os.path.join(app.static_folder, rel)
        if not os.path.exists(filesystem_path):
            # heurística
            base = os.path.basename(img).lower()
            if 'zombie' in base or 'zombies' in base:
                p.img = '/static/img/Imagenes/gta6.png'
            else:
                p.img = '/static/img/Imagenes/placeholder.svg'
            changed += 1
    if changed > 0:
        db.session.commit()


@app.route('/')
def root():
    # Renderiza la plantilla Jinja index.html en app/templates
    # Pasar los productos desde la base de datos para que la vista sea dinámica
    try:
        q = request.args.get('q', '').strip()
        if q:
            products = Product.query.filter((Product.title.ilike(f"%{q}%")) | (Product.category.ilike(f"%{q}%"))).order_by(Product.id.desc()).all()
        else:
            products = Product.query.order_by(Product.id.desc()).all()
    except Exception:
        products = []
    return render_template('index.html', products=products)


def _cart_from_session():
    return session.setdefault('cart', {})


@app.route('/cart/add', methods=['POST'])
def cart_add():
    # Accept form or JSON
    data = request.form or request.get_json() or {}
    pid = data.get('pid') or data.get('product_id')
    qty = data.get('qty') or data.get('quantity') or 1
    # CSRF check for AJAX
    if not validate_csrf(get_request_csrf_token()):
        return jsonify({'error': 'CSRF token missing or invalid'}), 400
    try:
        pid = int(pid)
        qty = int(qty)
    except Exception:
        return jsonify({'error': 'invalid parameters'}), 400
    p = Product.query.get(pid)
    if not p:
        return jsonify({'error': 'product not found'}), 404
    cart = _cart_from_session()
    cart[str(pid)] = cart.get(str(pid), 0) + max(1, qty)
    session['cart'] = cart
    # return JSON so frontend can update without reload
    total_items = sum(cart.values())
    return jsonify({'ok': True, 'total_items': total_items, 'product_id': pid})


@app.route('/cart')
def view_cart():
    cart = session.get('cart', {})
    items = []
    total = 0.0
    for pid_str, qty in cart.items():
        try:
            pid = int(pid_str)
        except Exception:
            continue
        p = Product.query.get(pid)
        if not p:
            continue
        subtotal = (p.price or 0.0) * qty
        items.append({'id': p.id, 'title': p.title, 'price': p.price, 'img': p.img, 'qty': qty, 'subtotal': subtotal, 'category': getattr(p, 'category', None)})
        total += subtotal
    return render_template('Carrito.html', cart_items=items, subtotal=total, total=total)


@app.route('/cart/remove', methods=['POST'])
def cart_remove():
    # CSRF check for AJAX
    if not validate_csrf(get_request_csrf_token()):
        return jsonify({'error': 'CSRF token missing or invalid'}), 400
    data = request.get_json() or request.form or {}
    pid = data.get('pid')
    try:
        pid = int(pid)
    except Exception:
        return jsonify({'error': 'invalid pid'}), 400
    cart = session.get('cart', {})
    if str(pid) in cart:
        cart.pop(str(pid), None)
        session['cart'] = cart
    return jsonify({'ok': True, 'total_items': sum(cart.values())})

@app.route('/favorites', methods=['GET'])
def view_favorites():
    favs = session.get('favorites', [])
    return jsonify({'favorites': list(favs)})

@app.route('/favorites/toggle', methods=['POST'])
def favorites_toggle():
    # CSRF check
    if not validate_csrf(get_request_csrf_token()):
        return jsonify({'error': 'CSRF token missing or invalid'}), 400
    data = request.get_json() or request.form or {}
    pid = data.get('pid') or data.get('product_id')
    try:
        pid = int(pid)
    except Exception:
        return jsonify({'error': 'invalid pid'}), 400
    favs = set(session.get('favorites', []))
    if str(pid) in favs:
        favs.discard(str(pid))
        action = 'removed'
    else:
        favs.add(str(pid))
        action = 'added'
    session['favorites'] = list(favs)
    return jsonify({'ok': True, 'action': action, 'pid': pid, 'total': len(favs)})

@app.route('/templates/<path:name>')
def template_view(name):
    # Renderiza archivos que están en app/templates
    # Prevent public rendering of admin templates via this generic endpoint.
    if name.startswith('admin/'):
        abort(403)
    return render_template(name)


@app.route('/favoritos')
def favoritos_page():
    # Render the favoritos page dynamically using session favorites
    favs = session.get('favorites', []) or []
    ids = []
    try:
        ids = [int(x) for x in favs]
    except Exception:
        ids = []
    products = []
    if ids:
        products = Product.query.filter(Product.id.in_(ids)).all()
    return render_template('favoritos.html', products=products)


@app.route('/pedidos')
def pedidos_page():
    # Show user's orders; require login
    if not session.get('user_id'):
        return redirect(url_for('login'))
    uid = session.get('user_id')
    try:
        orders = Order.query.filter_by(user_id=uid).order_by(Order.created_at.desc()).all()
    except Exception:
        orders = []
    return render_template('pedidos.html', orders=orders)


@app.route('/juegos')
def juegos_page():
    return redirect(url_for('category_page', slug='juegos'))


@app.route('/consolas')
def consolas_page():
    return redirect(url_for('category_page', slug='consolas'))


@app.route('/accesorios')
def accesorios_page():
    return redirect(url_for('category_page', slug='accesorios'))


@app.route('/controles')
def controles_page():
    return redirect(url_for('category_page', slug='controles'))



@app.route('/category/<slug>')
def category_page(slug):
    # Map friendly slugs to canonical category names stored in the DB
    mapping = {
        'juegos': 'Juegos',
        'consolas': 'Consolas',
        'accesorios': 'Accesorios',
        'controles': 'Controles'
    }
    cat_name = mapping.get(slug.lower(), None)
    try:
        if cat_name:
            products = Product.query.filter_by(category=cat_name).order_by(Product.id.desc()).all()
        else:
            # fallback: try case-insensitive match
            products = Product.query.filter(Product.category.ilike(f"%{slug}%")).order_by(Product.id.desc()).all()
    except Exception:
        products = []
    # Prefer templates named after the slug if present, otherwise fallback to a generic template
    tpl_name = f"{slug}.html"
    if os.path.exists(os.path.join(app.template_folder, tpl_name)):
        return render_template(tpl_name, products=products)
    return render_template('juegos.html', products=products)


@app.route('/app/static/<path:filename>')
def app_static(filename):
    # Sirve la carpeta app/static bajo la ruta /app/static/... para conservar rutas actuales
    return send_from_directory(os.path.join('app', 'static'), filename)


# Note: admin UI route is implemented further down and protected by admin_required.
# The previous placeholder route was removed to avoid duplicate registrations.


@app.route('/login', methods=['GET', 'POST'])
def login():
    # GET -> mostrar formulario (ya existe en templates/login.html)
    if request.method == 'GET':
        return render_template('login.html')

    # POST -> intentar autenticar
    # aceptar form-data o JSON
    data = request.form or request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()

    # Intentar autenticar contra la tabla users
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = bool(user.is_admin)
        if user.is_admin:
            return redirect(url_for('admin_dashboard'), code=303)
        return redirect(url_for('template_view', name='perfiluser.html'))

    # Credenciales inválidas
    return render_template('login.html', error='Credenciales inválidas')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'GET':
        return render_template('registro.html')
    # POST -> create user
    data = request.form or request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = (data.get('password') or '').strip()
    form_csrf = (data.get('csrf_token') if isinstance(data, dict) else request.form.get('csrf_token'))
    if not validate_csrf(form_csrf):
        abort(400, 'CSRF token missing or invalid')
    if not username or not password:
        return render_template('registro.html', error='Username y password requeridos')
    if User.query.filter_by(username=username).first():
        return render_template('registro.html', error='Usuario ya existe')
    u = User(username=username)
    u.set_password(password)
    db.session.add(u)
    db.session.commit()
    # auto-login
    session['user_id'] = u.id
    session['username'] = u.username
    session['is_admin'] = bool(u.is_admin)
    return redirect(url_for('perfiluser'))


@app.route('/perfiluser')
def perfiluser():
    uid = session.get('user_id')
    if not uid:
        return redirect(url_for('login'))
    user = User.query.get(uid)
    orders = Order.query.filter_by(user_id=uid).order_by(Order.created_at.desc()).all()
    favorites = session.get('favorites', [])
    return render_template('perfiluser.html', user=user, orders=orders, favorites_count=len(favorites))



@app.route('/admin_templates/<path:filename>')
def serve_admin_template_static(filename):
    # Legacy route: prefer templates placed in app/templates/admin/, otherwise fall back
    # to the old static admin_templates directory for backward compatibility.
    admin_tpl_path = os.path.join(app.template_folder, 'admin', filename)
    if os.path.exists(admin_tpl_path):
        # render the file from the admin subfolder
        return render_template(os.path.join('admin', filename))
    return send_from_directory(os.path.join('app', 'admin_templates'), filename)


@app.route('/api/products')
def api_products():
    try:
        products = Product.query.all()
        return jsonify([p.to_dict() for p in products])
    except OperationalError:
        # Si la BD no está inicializada, intenta crearla y devolver la lista vacía
        init_db_and_seed()
        products = Product.query.all()
        return jsonify([p.to_dict() for p in products])


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login'))
        if not session.get('is_admin'):
            abort(403)
        return f(*args, **kwargs)
    return decorated


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('is_admin', None)
    return redirect(url_for('root'))


# Protect admin route with decorator and render the admin templates from
# `app/templates/admin/` (new location). Falls back to old admin_templates dir.
@app.route('/admin')
@admin_required
def admin_dashboard():
    tpl_path = os.path.join(app.template_folder, 'admin', 'admin.html')
    if os.path.exists(tpl_path):
        return render_template('admin/admin.html')
    return send_from_directory(os.path.join('app', 'admin_templates'), 'admin.html')


@app.route('/admin/inventario.html', methods=['GET'])
@admin_required
def admin_inventario():
    # Render inventory page with products from DB
    products = Product.query.order_by(Product.id.desc()).all()
    return render_template('admin/inventario.html', products=products)


@app.route('/admin/inventario/nuevo', methods=['GET'])
@admin_required
def admin_inventario_new():
    # Render a separate page with the product creation form
    return render_template('admin/add_product.html')


def ensure_product_category_column():
    """Ensure the 'category' column exists in products table. If not, add it."""
    from sqlalchemy import inspect, text
    insp = inspect(db.engine)
    try:
        cols = [c['name'] for c in insp.get_columns('products')]
    except Exception:
        cols = []
    if 'category' not in cols:
        # Add column (use IF NOT EXISTS where supported)
        dialect = db.engine.dialect.name
        if dialect == 'postgresql':
            stmt = "ALTER TABLE products ADD COLUMN IF NOT EXISTS category VARCHAR(120);"
        else:
            # SQLite: simple ALTER ADD COLUMN works (no IF NOT EXISTS prior to 3.35)
            stmt = "ALTER TABLE products ADD COLUMN category VARCHAR(120);"
        try:
            with db.engine.begin() as conn:
                conn.execute(text(stmt))
            app.logger.info('Ensured category column with DDL: %s', stmt)
        except Exception as e:
            app.logger.warning('Could not add category column: %s', e)


def ensure_product_image_columns():
    """Ensure the 'image_data' and 'image_mime' columns exist in products table."""
    from sqlalchemy import inspect, text
    insp = inspect(db.engine)
    try:
        cols = [c['name'] for c in insp.get_columns('products')]
    except Exception:
        cols = []

    stmts = []
    if 'image_data' not in cols:
        # choose proper binary type per dialect
        dialect = db.engine.dialect.name
        if dialect == 'postgresql':
            stmts.append("ALTER TABLE products ADD COLUMN IF NOT EXISTS image_data BYTEA;")
        else:
            # SQLite and others: BLOB works for binary
            stmts.append("ALTER TABLE products ADD COLUMN image_data BLOB;")
    if 'image_mime' not in cols:
        dialect = db.engine.dialect.name
        if dialect == 'postgresql':
            stmts.append("ALTER TABLE products ADD COLUMN IF NOT EXISTS image_mime VARCHAR(120);")
        else:
            stmts.append("ALTER TABLE products ADD COLUMN image_mime VARCHAR(120);")

    # Execute DDL statements using SQLAlchemy 2.0 style (connection/transaction)
    for s in stmts:
        try:
            with db.engine.begin() as conn:
                conn.execute(text(s))
            app.logger.info('Executed DDL: %s', s)
        except Exception as e:
            # Log error so it's visible during startup; don't crash the app here
            app.logger.warning('Could not execute DDL (%s): %s', s, e)


@app.route('/admin/inventario/add', methods=['POST'])
@admin_required
def admin_inventario_add():
    # handle form submission from admin inventory page to create a new product
    title = (request.form.get('title') or '').strip()
    price = request.form.get('price') or '0'
    # handle uploaded image file (prefer upload over URL)
    img = None
    file = request.files.get('img_file')
    try:
        ensure_product_image_columns()
    except Exception:
        pass
    category = (request.form.get('category') or '').strip()
    # server-side validation for allowed categories
    allowed_categories = ['Consolas', 'Juegos', 'Accesorios', 'Controles']
    if category not in allowed_categories:
        # if an empty value was submitted, default to 'Juegos'
        if not category:
            category = 'Juegos'
        else:
            # unknown category submitted: normalize to General and warn
            flash(f"Categoría inválida '{category}' enviada. Se usará 'General'.")
            category = 'General'
    # CSRF protection
    form_csrf = request.form.get('csrf_token')
    if not validate_csrf(form_csrf):
        abort(400, 'CSRF token missing or invalid')

    if not title:
        return redirect(url_for('admin_inventario'))
    try:
        price_val = float(price)
    except Exception:
        price_val = 0.0

    # ensure category column exists before inserting
    try:
        ensure_product_category_column()
    except Exception:
        pass

    # image validation: only allow common image types and limit size to 2MB
    ALLOWED_MIMES = {'image/png', 'image/jpeg', 'image/jpg', 'image/webp'}
    MAX_IMAGE_BYTES = 2 * 1024 * 1024

    p = Product(title=title, price=price_val, img='/static/img/Imagenes/placeholder.svg')
    if file and file.filename:
        data = file.read()
        # validate size
        if len(data) > MAX_IMAGE_BYTES:
            flash('La imagen es demasiado grande. Tamaño máximo permitido: 2MB.')
            return redirect(url_for('admin_inventario'))
        # validate mime
        mim = (file.content_type or '').lower()
        if mim not in ALLOWED_MIMES:
            flash('Tipo de imagen no permitido. Use PNG, JPG o WEBP.')
            return redirect(url_for('admin_inventario'))
        p.image_data = data
        p.image_mime = mim or 'application/octet-stream'
    # set category if the model has that attribute
    try:
        setattr(p, 'category', category or 'General')
    except Exception:
        pass
    db.session.add(p)
    db.session.commit()
    flash('Producto creado correctamente.')
    return redirect(url_for('admin_inventario'))


@app.route('/admin/inventario/edit/<int:pid>', methods=['GET', 'POST'])
@admin_required
def admin_inventario_edit(pid):
    p = Product.query.get_or_404(pid)
    if request.method == 'GET':
        return render_template('admin/edit_product.html', product=p)
    # POST -> update
    form_csrf = request.form.get('csrf_token')
    if not validate_csrf(form_csrf):
        abort(400, 'CSRF token missing or invalid')
    title = (request.form.get('title') or '').strip()
    try:
        price_val = float(request.form.get('price') or 0)
    except Exception:
        price_val = 0.0
    img = (request.form.get('img') or '').strip()
    category = (request.form.get('category') or '').strip()
    # handle uploaded image
    file = request.files.get('img_file')
    try:
        ensure_product_image_columns()
    except Exception:
        pass
    if title:
        p.title = title
    p.price = price_val
    # if file uploaded, replace binary image; otherwise keep existing
    if file and file.filename:
        data = file.read()
        # validate size and type
        ALLOWED_MIMES = {'image/png', 'image/jpeg', 'image/jpg', 'image/webp'}
        MAX_IMAGE_BYTES = 2 * 1024 * 1024
        if len(data) > MAX_IMAGE_BYTES:
            flash('La imagen es demasiado grande. Tamaño máximo permitido: 2MB.')
            return redirect(url_for('admin_inventario_edit', pid=pid))
        mim = (file.content_type or '').lower()
        if mim not in ALLOWED_MIMES:
            flash('Tipo de imagen no permitido. Use PNG, JPG o WEBP.')
            return redirect(url_for('admin_inventario_edit', pid=pid))
        p.image_data = data
        p.image_mime = mim or 'application/octet-stream'
        # clear legacy img path
        p.img = '/static/img/Imagenes/placeholder.svg'
    else:
        p.img = img or p.img
    # validate category server-side
    allowed_categories = ['Consolas', 'Juegos', 'Accesorios', 'Controles']
    try:
        if category:
            if category in allowed_categories:
                setattr(p, 'category', category)
            else:
                flash(f"Categoría inválida '{category}' enviada. Se mantiene la categoría actual.")
        else:
            # keep existing or default
            setattr(p, 'category', p.__dict__.get('category') or 'General')
    except Exception:
        pass
    db.session.commit()
    flash('Producto actualizado correctamente.')
    return redirect(url_for('admin_inventario'))


@app.route('/admin/inventario/delete/<int:pid>', methods=['POST'])
@admin_required
def admin_inventario_delete(pid):
    form_csrf = request.form.get('csrf_token')
    if not validate_csrf(form_csrf):
        abort(400, 'CSRF token missing or invalid')
    p = Product.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    flash('Producto eliminado.')
    return redirect(url_for('admin_inventario'))


@app.route('/admin/<path:name>')
@admin_required
def admin_render(name):
    """Render admin templates from app/templates/admin/<name>.
    Falls back to legacy static admin_templates if the Jinja template is missing.
    """
    tpl = os.path.join('admin', name)
    try:
        # render_template accepts posix-like paths 'admin/juegos.html'
        return render_template(tpl)
    except Exception:
        # fallback: serve legacy static admin file
        static_path = os.path.join('app', 'admin_templates')
        return send_from_directory(static_path, name)


@app.route('/product_image/<int:pid>')
def product_image(pid):
    p = Product.query.get(pid)
    if not p:
        return send_from_directory(os.path.join(app.static_folder, 'img/Imagenes'), 'placeholder.svg')
    if p.image_data:
        from flask import make_response
        resp = make_response(p.image_data)
        resp.headers.set('Content-Type', p.image_mime or 'application/octet-stream')
        return resp
    # fallback to legacy path if present
    if p.img:
        # if p.img is a static path like /static/..., redirect
        if p.img.startswith('/'):
            return redirect(p.img)
        return send_from_directory(app.static_folder, p.img)
    return send_from_directory(os.path.join(app.static_folder, 'img/Imagenes'), 'placeholder.svg')


@app.errorhandler(IntegrityError)
def handle_integrity_error(e):
    # Roll back the failed transaction and return a friendly message
    try:
        db.session.rollback()
    except Exception:
        pass
    app.logger.exception('Database integrity error')
    msg = 'Error de integridad en la base de datos.'
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'error': msg}), 400
    flash(msg)
    return redirect(url_for('root'))


if __name__ == '__main__':
    # Inicializa BD si es necesario y arranca el servidor
    try:
        init_db_and_seed()
        try:
            ensure_product_image_columns()
            ensure_product_category_column()
        except Exception:
            pass
    except Exception:
        pass

    app.run(debug=True, host='0.0.0.0', port=5000)
try:
    with app.app_context():
        init_db_and_seed()
        try:
            ensure_product_image_columns()
            ensure_product_category_column()
        except Exception:
            pass
except Exception:
    # Ignora errores en entornos donde la DB no se puede crear ahora
    pass


@app.route('/api/products', methods=['POST'])
def api_create_product():
    data = request.get_json() or {}
    title = data.get('title')
    price = data.get('price', 0)
    img = data.get('img')
    if not title:
        return jsonify({'error': 'title required'}), 400
    p = Product(title=title, price=price, img=img)
    db.session.add(p)
    db.session.commit()
    return jsonify(p.to_dict()), 201


@app.route('/api/products/<int:pid>', methods=['GET', 'PUT', 'DELETE'])
def api_product_detail(pid):
    p = Product.query.get(pid)
    if not p:
        abort(404)
    if request.method == 'GET':
        return jsonify(p.to_dict())
    if request.method == 'PUT':
        data = request.get_json() or {}
        p.title = data.get('title', p.title)
        p.price = data.get('price', p.price)
        p.img = data.get('img', p.img)
        db.session.commit()
        return jsonify(p.to_dict())
    if request.method == 'DELETE':
        db.session.delete(p)
        db.session.commit()
        return ('', 204)


@app.route('/checkout', methods=['POST'])
def checkout():
    """Create an Order from the session cart. Accepts AJAX (JSON) or form posts.
    CSRF-protected via get_request_csrf_token() / validate_csrf().
    """
    # CSRF check for AJAX/form
    token = get_request_csrf_token()
    if not validate_csrf(token):
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'CSRF token missing or invalid'}), 400
        abort(400, 'CSRF token missing or invalid')

    cart = session.get('cart', {}) or {}
    if not cart:
        # nothing to checkout
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': 'cart empty'}), 400
        flash('El carrito está vacío.')
        return redirect(url_for('view_cart'))

    # Create order and order items
    order = Order(user_id=session.get('user_id'))
    db.session.add(order)
    db.session.flush()  # get order.id

    total = 0.0
    for pid_str, qty in list(cart.items()):
        try:
            pid = int(pid_str)
            qty = int(qty)
        except Exception:
            continue
        product = Product.query.get(pid)
        if not product:
            continue
        price = float(product.price or 0.0)
        oi = OrderItem(order_id=order.id, product_id=product.id, quantity=qty, price=price)
        db.session.add(oi)
        total += price * qty

    order.total = total
    db.session.commit()

    # clear cart
    session.pop('cart', None)

    # Respond JSON for AJAX requests, otherwise render the final page
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.accept_json:
        return jsonify({'ok': True, 'order_id': order.id, 'total': total})

    flash('Compra completada. Gracias por su compra.')
    return render_template('CompraFinalizada.html', order=order)


@app.route('/pagar')
def pagar_page():
    # Render payment screen, similar to view_cart but present payment form
    cart = session.get('cart', {})
    items = []
    total = 0.0
    for pid_str, qty in cart.items():
        try:
            pid = int(pid_str)
            qty = int(qty)
        except Exception:
            continue
        p = Product.query.get(pid)
        if not p:
            continue
        subtotal = (p.price or 0.0) * qty
        items.append({'id': p.id, 'title': p.title, 'price': p.price, 'img': p.img, 'qty': qty, 'subtotal': subtotal, 'category': getattr(p, 'category', None)})
        total += subtotal
    return render_template('Pagar.html', cart_items=items, subtotal=total, total=total)
