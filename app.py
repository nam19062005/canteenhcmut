from flask import Flask, jsonify, request, render_template
from models import db, Canteen, Category, Food, Order, OrderItem
import random
import string
from datetime import datetime # Thư viện để xử lý thời gian cho thống kê

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///canteen.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
with app.app_context():
    db.create_all()

# ==========================================
# CÁC ROUTE GIAO DIỆN
# ==========================================
@app.route('/')
def home(): return render_template('index.html')

@app.route('/admin/dashboard')
def dashboard(): return render_template('dashboard.html')

@app.route('/staff')
def staff(): return render_template('staff.html')

# ==========================================
# API - KHÁCH HÀNG
# ==========================================
@app.route('/api/menu', methods=['GET'])
def get_menu():
    canteen_id = request.args.get('canteen_id', 1)
    category_id = request.args.get('category_id')
    search_query = request.args.get('search', '').strip() 
    
    query = Food.query.filter_by(canteen_id=canteen_id)
    
    if category_id: 
        query = query.filter_by(category_id=category_id)
        
    if search_query:
        query = query.filter(Food.name.ilike(f'%{search_query}%'))
        
    foods = query.all()
    return jsonify([{
        "id": f.id, "name": f.name, "price": f.price, 
        "quantity": f.quantity, "category": f.category.name if f.category else "",
        "image_url": f.image_url if f.image_url else ""
    } for f in foods]), 200

@app.route('/api/order', methods=['POST'])
def create_order():
    data = request.get_json()
    items_data = data.get('items', [])
    if not items_data: return jsonify({"error": "Giỏ hàng trống"}), 400

    order_code = f"HCMUT_{''.join(random.choices(string.ascii_uppercase + string.digits, k=5))}"
    new_order = Order(order_code=order_code, total_price=0)
    db.session.add(new_order)
    db.session.flush()

    total = 0
    for item in items_data:
        food = Food.query.get(item['food_id'])
        if food and food.quantity >= item['quantity']:
            food.quantity -= item['quantity']
            total += food.price * item['quantity']
            db.session.add(OrderItem(order_id=new_order.id, food_id=food.id, quantity=item['quantity']))
        else:
            db.session.rollback()
            return jsonify({"error": f"Món {food.name if food else 'không xác định'} không đủ hàng"}), 400

    new_order.total_price = total
    db.session.commit()
    return jsonify({"order_code": new_order.order_code, "total": total}), 201

# ==========================================
# API - MANAGER (QUẢN LÝ)
# ==========================================
@app.route('/api/admin/stats', methods=['GET'])
def get_stats():
    filter_type = request.args.get('filter', 'all')
    
    # Bắt đầu truy vấn với các đơn hàng đã hoàn thành
    query = Order.query.filter_by(status='Completed')
    now = datetime.utcnow()
    
    if filter_type == 'today':
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        query = query.filter(Order.created_at >= start_of_day)
    elif filter_type == 'month':
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        query = query.filter(Order.created_at >= start_of_month)

    # Lấy tổng doanh thu và đếm số lượng đơn
    total_rev = query.with_entities(db.func.sum(Order.total_price)).scalar() or 0
    total_orders = query.count()
    
    return jsonify({"revenue": total_rev, "orders": total_orders})

@app.route('/api/admin/inventory', methods=['GET'])
def get_inventory():
    foods = Food.query.all()
    return jsonify([{
        "id": f.id, "name": f.name, "price": f.price, "quantity": f.quantity,
        "canteen_id": f.canteen_id, "canteen": f.canteen.name if f.canteen else "N/A",
        "category_id": f.category_id, "image_url": f.image_url if f.image_url else ""
    } for f in foods]), 200

@app.route('/api/admin/form-data', methods=['GET'])
def get_form_data():
    categories = Category.query.all()
    canteens = Canteen.query.all()
    return jsonify({
        "categories": [{"id": c.id, "name": c.name} for c in categories],
        "canteens": [{"id": c.id, "name": c.name} for c in canteens]
    }), 200

@app.route('/api/admin/food', methods=['POST'])
def add_food():
    data = request.get_json()
    name = data.get('name')
    price = data.get('price')
    quantity = data.get('quantity', 0)
    canteen_id = data.get('canteen_id')
    category_id = data.get('category_id')
    image_url = data.get('image_url')

    if not all([name, price, canteen_id, category_id]):
        return jsonify({"error": "Vui lòng điền đủ thông tin bắt buộc"}), 400

    new_food = Food(
        name=name, price=float(price), quantity=int(quantity),
        canteen_id=int(canteen_id), category_id=int(category_id),
        image_url=image_url
    )
    db.session.add(new_food)
    db.session.commit()
    return jsonify({"message": "Thêm món thành công!"}), 201

@app.route('/api/admin/food/<int:food_id>', methods=['PUT'])
def edit_food(food_id):
    food = Food.query.get(food_id)
    if not food: return jsonify({"error": "Không tìm thấy món ăn"}), 404

    data = request.get_json()
    if 'name' in data: food.name = data['name']
    if 'price' in data: food.price = float(data['price'])
    if 'quantity' in data: food.quantity = int(data['quantity'])
    if 'canteen_id' in data: food.canteen_id = int(data['canteen_id'])
    if 'category_id' in data: food.category_id = int(data['category_id'])
    if 'image_url' in data: food.image_url = data['image_url']

    db.session.commit()
    return jsonify({"message": "Cập nhật thông tin thành công!"}), 200

# ==========================================
# API - STAFF (NHÂN VIÊN)
# ==========================================
@app.route('/api/staff/orders', methods=['GET'])
def get_orders():
    orders = Order.query.order_by(
        db.case((Order.status == 'Pending', 0), else_=1),
        Order.created_at.desc()
    ).all()
    
    result = []
    for o in orders:
        items_list = [{"name": item.food.name, "quantity": item.quantity} for item in o.items]
        result.append({
            "id": o.id, "order_code": o.order_code, "total_price": o.total_price,
            "status": o.status, "created_at": o.created_at.strftime("%H:%M %d/%m/%Y"),
            "items": items_list
        })
    return jsonify(result), 200

@app.route('/api/staff/order/<int:order_id>/complete', methods=['POST'])
def complete_order(order_id):
    order = Order.query.get(order_id)
    if order:
        order.status = 'Completed'
        db.session.commit()
        return jsonify({"message": "Đã xác nhận giao hàng!"}), 200
    return jsonify({"error": "Lỗi"}), 404

@app.route('/api/staff/order/<int:order_id>/cancel', methods=['POST'])
def cancel_order(order_id):
    order = Order.query.get(order_id)
    if order and order.status == 'Pending':
        for item in order.items:
            if item.food: item.food.quantity += item.quantity
        order.status = 'Cancelled'
        db.session.commit()
        return jsonify({"message": "Đã hủy đơn hàng!"}), 200
    return jsonify({"error": "Lỗi"}), 400

if __name__ == '__main__':
    app.run(debug=True)