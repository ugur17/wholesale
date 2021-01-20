import os
import secrets
import datetime
from flask import Flask, render_template, url_for, flash, redirect, request, session, abort
from forms import RegistrationForm, LoginForm, UpdateCustomerForm, UpdateStoreForm, ProductForm, RegistrationDetailForm, CartForm, SearchForm, PriorityForm, WHOIS_CHOICES, MATERIAL_CHOICES
import mysql.connector
from flask_bcrypt import Bcrypt
from dbinit import INIT_STATEMENTS

mydb= mysql.connector.connect(
    host="localhost",
    user="root",
    password="123456",
    database="wholesale"
)

mycursor = mydb.cursor(dictionary=True)

app = Flask(__name__)
bcrypt = Bcrypt(app)

app.config['SECRET_KEY'] = 'b1abd0a3907f0346776c70e58ccdf359'


for statement in INIT_STATEMENTS:  #dbinitten create komutlarını alıyor loopta tek tek execute ediyor
    mycursor.execute(statement)  #komutları çalıştırma kodu
    mydb.commit()
        
@app.route('/')
@app.route('/home')
def home():
    mycursor.execute('SELECT * FROM product')
    products = mycursor.fetchall()
    ordered_products = []
    mycursor.execute('SELECT * FROM store ORDER BY priority DESC')
    stores = mycursor.fetchall()
    for store in stores:
        mycursor.execute('SELECT * FROM product WHERE store_id = {}'.format(store['id']))
        adding_p = mycursor.fetchall()
        if adding_p:
            for item in adding_p:
                item['store_name'] = store['store_name']
                item['store_phone'] = store['phone']
                ordered_products.append(item)
    return render_template('home.html', title='Products', products=ordered_products)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'loggedin' not in session:
        form = RegistrationForm()
        if form.validate_on_submit():
            account_phone = []
            mycursor.execute('SELECT * FROM customer WHERE phone = %s', (form.phone.data,))
            customer_phone = mycursor.fetchone()
            mycursor.execute('SELECT * FROM store WHERE phone = %s', (form.phone.data,))
            store_phone = mycursor.fetchone()
            if customer_phone or store_phone:
                flash(f'There already exists this phone number { form.phone.data }!', 'danger')
            else:
                hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
                if form.whois.data == '1':
                    now = datetime.datetime.utcnow()
                    mycursor.execute('INSERT INTO customer(name, phone, password, register_date) VALUES (%s, %s, %s, %s)', (form.name.data, form.phone.data, hashed_password, now.strftime('%Y-%m-%d %H:%M:%S'),))
                    session['name'] = form.name.data
                    session['phone'] = form.phone.data
                    session['hashed_password'] = hashed_password
                    session['whois'] = form.whois.data
                    mydb.commit()
                    flash(f'Account created for { form.name.data }! You can access the system.', 'success')
                    return redirect(url_for('login'))
                elif form.whois.data == '2':
                    session['name'] = form.name.data
                    session['phone'] = form.phone.data
                    session['hashed_password'] = hashed_password
                    session['whois'] = form.whois.data
                    flash(f'Account created successfully! Please enter the store informations.', 'success')
                    return redirect(url_for('register_detail'))
        return render_template('register.html', title='Register', form = form)
    else:
        flash("You've already logged in!", 'success')
        return redirect(url_for('home'))

@app.route('/register_detail', methods=['GET', 'POST'])
def register_detail():
    if 'loggedin' not in session:
        form = RegistrationDetailForm()
        if form.validate_on_submit():
            mycursor.execute('INSERT INTO store(store_name, address, name, phone, password) VALUES (%s, %s, %s, %s, %s)', (form.store_name.data, form.store_address.data, session['name'], session['phone'], session['hashed_password'],))
            mydb.commit()
            flash(f'Registration completed for { form.store_name.data }! You can access the system.', 'success')
            return redirect(url_for('login'))
        return render_template('register_detail.html', title='Store Informations', form=form)
    else:
        flash("You've already logged in!", 'success')
        return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'loggedin' not in session:
        form = LoginForm()
        if form.validate_on_submit():
            account = []
            if form.whois.data == '1':
                mycursor.execute('SELECT * FROM customer WHERE phone = %s', (form.phone.data,))
                account = mycursor.fetchone()
            elif form.whois.data == '2':
                mycursor.execute('SELECT * FROM store WHERE phone = %s', (form.phone.data,))
                account = mycursor.fetchone()
            if account and bcrypt.check_password_hash(account['password'], form.password.data):
                session['loggedin'] = True
                session['whois'] = form.whois.data
                session['id'] = account['id']
                session['name'] = account['name']
                session['phone'] = account['phone']
                session['photo'] = account['photo']
                if form.whois.data == '2':
                    session['store_name'] = account['store_name']
                    session['address'] = account['address']
                flash(f"You've logged in for { session['name'] }!", 'success')
                return redirect(url_for('home'))
            else:
                # Account doesnt exist or username/password incorrect
                msg = 'Incorrect username/password!'
                flash(msg, 'danger')
        return render_template('login.html', title='Login', form = form)
    else:
        flash("You've already logged in!", 'success')
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    if session['whois'] == '2':
        session.pop('store_name', None)
        session.pop('address', None)
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('whois', None)
    session.pop('name', None)
    session.pop('phone', None)
    session.pop('photo', None)
    session.pop('cart', None)
    return redirect(url_for('login'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8) # to keep the name of the picture (in order to prevent from name collision)
    f_name, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    form_picture.save(picture_path)
    return picture_fn

@app.route('/product/new', methods=['GET', 'POST'])
def new_product():
    form = ProductForm()
    if session['whois'] == '2':
        if form.validate_on_submit():
            material = dict(MATERIAL_CHOICES)[form.material.data]
            if form.photo.data:
                picture_file = save_picture(form.photo.data)
            mycursor.execute('SELECT * FROM product WHERE store_id = %s AND product_name = %s', (session['id'], form.name.data,))
            exist_product = mycursor.fetchone()
            if exist_product:
                flash("There already exists this product in your store!", 'warning')
                return redirect(url_for('new_product'))
            else:
                if form.photo.data:
                    now = datetime.datetime.utcnow()
                    mycursor.execute('INSERT INTO product(store_id, product_name, material_type, price, color, changing_date, photo) VALUES (%s, %s, %s, %s, %s, %s, %s)', (session['id'], form.name.data, material, form.price.data,  form.color.data, now.strftime('%Y-%m-%d %H:%M:%S'), picture_file,))
                    mydb.commit()
                else:
                    now = datetime.datetime.utcnow()
                    mycursor.execute('INSERT INTO product(store_id, product_name, material_type, price, color, changing_date) VALUES (%s, %s, %s, %s, %s, %s)', (session['id'], form.name.data, material, form.price.data,  form.color.data, now.strftime('%Y-%m-%d %H:%M:%S'),))
                    mydb.commit()
                flash("New product added!", 'success')
                return redirect(url_for('home'))
        return render_template('new_product.html', title='New Product', form=form, legend = 'Add Product')
    else:
        flash("Firstly, you need to create a virtual store!", 'warning')
        return redirect(url_for('home'))

@app.route('/product/<int:product_id>', methods=['GET', 'POST'])
def single_product(product_id):
    form = CartForm()
    mycursor.execute('SELECT * FROM product WHERE product_id = {}'.format(product_id))
    product = mycursor.fetchone()
    if product == None:
        abort(404)
    mycursor.execute('SELECT * FROM store WHERE id = {}'.format(product['store_id']))
    store = mycursor.fetchone()
    product['store_name'] = store['store_name']
    product['store_phone'] = store['phone']
    image_file = url_for('static', filename='profile_pics/' +  product['photo'] )
    if 'whois' in session and session['whois'] == '1':
        if form.validate_on_submit():
            if 'cart' in session:
                if not any(str(product['product_id']) in d for d in session['cart']):
                    new_dict = {product['product_id']: form.quantity.data}
                    keys_values = new_dict.items()
                    new_d = {str(key): value for key, value in keys_values}
                    new_dict_copy = new_d.copy()
                    session['cart'].append(new_dict_copy)
                    flash("New Product Added to Cart!", 'success')
                elif any(str(product['product_id']) in d for d in session['cart']):
                    for d in session['cart']:
                        for k, v in d.items():
                            if k == str(product['product_id']):
                                d.update({k: form.quantity.data})
                    flash("Quantity updated!", 'success')
            else:
                session['cart'] = [{product['product_id']: form.quantity.data}]
                flash("New Product Added to Cart!", 'success')
            return redirect(url_for('shopping_cart'))
    return render_template('single_product.html', image_file=image_file, title=product['product_name'], product=product, form=form)

@app.route('/product/<int:product_id>/update', methods=['GET', 'POST'])
def update_product(product_id):
    form = ProductForm()
    mycursor.execute('SELECT * FROM product WHERE product_id = {}'.format(product_id))
    product = mycursor.fetchone()
    mycursor.execute('SELECT * FROM store WHERE id = {}'.format(product['store_id']))
    store = mycursor.fetchone()
    if store['id'] != session['id']:
        abort(403)
    if form.validate_on_submit():
        new_name = form.name.data
        new_material = dict(MATERIAL_CHOICES)[form.material.data]
        new_color = form.color.data
        new_price = form.price.data
        if form.photo.data:
            new_photo = save_picture(form.photo.data)
            mycursor.execute('UPDATE product SET photo = %s WHERE product_id = %s', (new_photo, product_id,))
        now = datetime.datetime.utcnow()
        mycursor.execute('UPDATE product SET product_name = %s, material_type = %s, color = %s, price = %s, changing_date = %s WHERE product_id = %s', (new_name, new_material, new_color, new_price, now.strftime('%Y-%m-%d %H:%M:%S'), product_id,))
        mydb.commit()
        flash("Product Updated!", 'success')
        return redirect(url_for('single_product', product_id = product_id))
    if request.method == 'GET':
        form.name.data = product['product_name']
        form.material.data = product['material_type']
        form.color.data = product['color']
        form.price.data = product['price']
    return render_template('new_product.html', title='Update Product', form=form, legend='Update Product')

@app.route('/product/<int:product_id>/delete', methods = ['POST'])
def delete_product(product_id):
    mycursor.execute('SELECT * FROM product WHERE product_id = {}'.format(product_id))
    product = mycursor.fetchone()
    mycursor.execute('SELECT * FROM store WHERE id = {}'.format(product['store_id']))
    store = mycursor.fetchone()
    if store['id'] != session['id']:
        abort(403)
    mycursor.execute('DELETE FROM product WHERE product_id = {}'.format(product_id))
    mydb.commit()
    flash("Product Deleted!", 'success')
    return redirect(url_for('home'))

@app.route('/account_customer', methods=['GET', 'POST'])
def account_customer():
    form = UpdateCustomerForm()
    if session['whois'] == '1':
        if form.validate_on_submit():
            account_phone = [] #initilialize
            new_name = form.name.data # take data from the form
            new_phone = form.phone.data # take data from the form
            mycursor.execute('SELECT * FROM customer WHERE phone = %s', (new_phone,))
            account_phone = mycursor.fetchone()       
            if account_phone and account_phone['phone'] != session['phone']:
                flash(f'There already exists this phone number { form.phone.data }!', 'danger')
            else:
                if form.picture.data:
                    picture_file = save_picture(form.picture.data)
                    mycursor.execute('UPDATE customer SET photo = %s WHERE id = %s', (picture_file, session['id'],))
                    session['photo'] = picture_file
                mycursor.execute('UPDATE customer SET name = %s, phone = %s WHERE id = %s', (new_name, new_phone, session['id'],))
                session['name'] = new_name
                session['phone'] = new_phone
                mydb.commit()
                flash('Account updated!', 'success')
                return redirect(url_for('account_customer'))
        elif request.method == 'GET':
            form.name.data = session['name']
            form.phone.data = session['phone']
        mycursor.execute('SELECT * FROM customer WHERE phone = %s', (session['phone'],))
        account = mycursor.fetchone()
        mycursor.execute('SELECT * FROM store WHERE id = %s', (account['fav_store_id'],))   
        fav_store = mycursor.fetchone()
        registration_date = account['register_date']
        image_file = url_for('static', filename='profile_pics/' + session['photo'])
        if fav_store:
            return render_template('account_customer.html', title='Account', image_file=image_file, form=form, fav_store=fav_store['store_name'], registration_date=registration_date)
        else:
            return render_template('account_customer.html', title='Account', image_file=image_file, form=form, registration_date=registration_date)
    else:
        flash("Firstly you need to log in!", 'warning')
        return redirect(url_for('login'))

@app.route('/delete_customer', methods=['POST'])
def delete_customer():
    if session['whois'] == '1':
        mycursor.execute('DELETE FROM customer WHERE id = {}'.format(session['id']))
        mydb.commit()
        flash('You deleted the account', 'success')
        return redirect(url_for('logout'))
    else:
        abort(403)

@app.route('/account_store', methods=['GET', 'POST'])
def account_store():
    form = UpdateStoreForm()
    if session['whois'] == '2':
        if form.validate_on_submit():
            account_phone = [] #initilialize
            new_store_name = form.store_name.data
            new_address = form.store_address.data
            new_owner_name = form.owner_name.data # take data from the form
            new_phone = form.phone.data # take data from the form
            mycursor.execute('SELECT * FROM store WHERE phone = %s', (new_phone,))
            account_phone = mycursor.fetchone()       
            if account_phone and account_phone['phone'] != session['phone']:
                flash(f'There already exists this phone number { form.phone.data }!', 'danger')
            else:
                if form.picture.data:
                    picture_file = save_picture(form.picture.data)
                    mycursor.execute('UPDATE store SET photo = %s WHERE id = %s', (picture_file, session['id'],))
                    session['photo'] = picture_file
                mycursor.execute('UPDATE store SET store_name = %s, address = %s, name = %s, phone = %s  WHERE id = %s', (new_store_name, new_address, new_owner_name, new_phone, session['id'],))
                session['store_name'] = new_store_name
                session['address'] = new_address
                session['name'] = new_owner_name
                session['phone'] = new_phone
                mydb.commit()
                flash('Account updated!', 'success')
                return redirect(url_for('account_store'))
        elif request.method == 'GET':
            form.store_name.data = session['store_name']
            form.store_address.data = session['address']
            form.owner_name.data = session['name']
            form.phone.data = session['phone']
        mycursor.execute('SELECT * FROM store WHERE phone = %s', (session['phone'],))
        account = mycursor.fetchone()
        image_file = url_for('static', filename='profile_pics/' + session['photo'])
        return render_template('account_store.html', title='Account', image_file=image_file, form=form, store=account)
    else:
        flash("Firstly you need to log in!", 'warning')
        return redirect(url_for('login'))

@app.route('/delete_store', methods=['POST'])
def delete_store():
    if session['whois'] == '2':
        mycursor.execute('DELETE FROM store WHERE id = {}'.format(session['id']))
        mydb.commit()
        flash('You deleted the account', 'success')
        return redirect(url_for('logout'))
    else:
        abort(403)

@app.route('/store_info/<int:store_id>')
def store_info(store_id):
    mycursor.execute('SELECT * FROM store WHERE id = {}'.format(store_id))
    store = mycursor.fetchone()
    if store == None:
        abort(404)
    image_file = url_for('static', filename='profile_pics/' +  store['photo'] )
    return render_template('store_info.html', image_file=image_file, title=store['store_name'], store=store)

@app.route('/shopping_chart')
def shopping_cart():
    if 'whois' not in session or session['whois'] != '1':
        abort(403)
    form = CartForm()
    products = []
    total_price = 0
    if 'cart' in session:
        for d in session['cart']:
            for k, v in d.items():
                mycursor.execute('SELECT * FROM product WHERE product_id = %s', (k,))
                product = mycursor.fetchone()
                product['quantity'] = v
                total_price = total_price + (product['quantity'] * product['price'])
                products.append(product)
    return render_template('shopping_cart.html', title='Shopping Cart', products=products, form=form, total_price=total_price)

@app.route('/remove_from_cart/<int:product_id>', methods = ['POST'])
def remove_from_cart(product_id):
    if 'whois' not in session or session['whois'] != '1':
        abort(403)
    for i, j in enumerate(session['cart']):
        for k, v in j.items():
            if k == str(product_id):
                del session['cart'][i]
                flash("Successfully removed!", 'success')
    return redirect(url_for('shopping_cart'))

@app.route('/confirm_order', methods = ['POST'])
def confirm_order():
    if 'whois' not in session or session['whois'] != '1':
        abort(403)
    total_price = 0
    now = datetime.datetime.utcnow()
    mycursor.execute('INSERT INTO orders(customer_id, order_date) VALUES (%s, %s)', (session['id'], now.strftime('%Y-%m-%d %H:%M:%S'),))
    last_order_id = mycursor.lastrowid
    if 'cart' in session:
        for d in session['cart']:
            for k, v in d.items():
                mycursor.execute('SELECT * FROM product WHERE product_id = %s', (k,))
                product = mycursor.fetchone()
                product['quantity'] = v
                total_price = (product['quantity'] * product['price'])
                mycursor.execute('INSERT INTO orderdetails(order_id, product_id, product_quantity, total_price) VALUES (%s, %s, %s, %s)', (last_order_id, product['product_id'], product['quantity'], total_price,))
    mydb.commit()
    session.pop('cart', None)
    flash('You successfully made order', 'success')
    return redirect(url_for('home'))

@app.route('/fav_store/<int:fav_store_id>')
def fav_store(fav_store_id):
    if 'whois' not in session or session['whois'] != '1':
        abort(403)
    mycursor.execute('UPDATE customer SET fav_store_id = %s WHERE id = %s', (fav_store_id, session['id'],))
    mydb.commit()
    flash('Successfully added to the favourite store!', 'success')
    return redirect(url_for('account_customer'))

@app.route('/remove_fav_store', methods=['POST'])
def remove_fav_store():
    if 'whois' not in session or session['whois'] != '1':
        abort(403)
    mycursor.execute('UPDATE customer SET fav_store_id = NULL WHERE id = %s', (session['id'],))
    mydb.commit()
    flash('Successfully removed the favourite store!', 'success')
    return redirect(url_for('account_customer'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    if request.method == 'POST' and form.validate_on_submit():
        who = form.who_search.data
        if who == '2':
            store_name = form.search.data
            mycursor.execute('SELECT * FROM store WHERE store_name = %s', (store_name,))
            stores = mycursor.fetchall()
            return render_template('search.html', title="Search", form=form, stores=stores)
        elif who == '1':
            customer_name = form.search.data
            mycursor.execute('SELECT * FROM customer WHERE name = %s', (customer_name,))
            customers = mycursor.fetchall()
            return render_template('search.html', title="Search", form=form, customers=customers)
    return render_template('search.html', title="Search", form=form)

@app.route('/take_p', methods=['GET', 'POST'])
def take_p():
    if 'whois' not in session or session['whois'] != '2':
        abort(403)
    form = PriorityForm()
    priority_price = 0
    mycursor.execute('SELECT * FROM store WHERE phone = %s', (session['phone'],))
    account = mycursor.fetchone()
    if request.method == 'POST' and form.validate_on_submit():
        priority = form.level.data
        diff = int(priority) - account['priority']
        if diff <= 0:
            priority_price = 0
        else:
            priority_price = diff * 100
        return render_template('take_p.html', form=form, title="Take Priority", price=priority_price, new_p=priority, current_p=account['priority'])
    return render_template('take_p.html', title="Take Priority", form=form, price=priority_price, new_p=account['priority'], current_p=account['priority'])

@app.route('/update_p/<int:priority>', methods = ['POST'])
def update_p(priority):
    if 'whois' not in session or session['whois'] != '2':
        abort(403)
    mycursor.execute('SELECT * FROM store WHERE phone = %s', (session['phone'],))
    account = mycursor.fetchone()
    if priority != account['priority']:
        mycursor.execute('UPDATE store SET priority = %s WHERE id = %s', (priority, session['id']))
        mydb.commit()
        flash('You successfully updated priority', 'success')
    else:
        flash('Priority remains same', 'warning')
    return redirect(url_for('account_store'))


if __name__ == '__main__':
    app.run(debug=True)