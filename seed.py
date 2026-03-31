from app import app
from models import db, Canteen, Category, Food

def seed_database():
    with app.app_context():
        if Canteen.query.first() is None:
            print("Đang nạp dữ liệu...")
            
            canteen_b4 = Canteen(name="Canteen B4", location="Tòa nhà B4")
            canteen_c5 = Canteen(name="Canteen C5", location="Tòa nhà C5")
            canteen_a4 = Canteen(name="Canteen A4", location="Tòa nhà A4")
            db.session.add_all([canteen_b4, canteen_c5, canteen_a4])
            db.session.commit() 
            
            cat_food = Category(name="Món chính")
            cat_drink = Category(name="Đồ uống")
            db.session.add_all([cat_food, cat_drink])
            db.session.commit()
            
            # Đã thêm link ảnh minh họa vào dữ liệu mẫu
            food1 = Food(name="Cơm sườn trứng", price=35000, quantity=50, canteen_id=canteen_b4.id, category_id=cat_food.id, image_url="https://images.unsplash.com/photo-1555529323-448102391038?w=400&h=300&fit=crop")
            food2 = Food(name="Bún bò Huế", price=40000, quantity=30, canteen_id=canteen_b4.id, category_id=cat_food.id, image_url="https://images.unsplash.com/photo-1610440042657-612c34d95e9f?w=400&h=300&fit=crop")
            drink1 = Food(name="Trà đá", price=5000, quantity=100, canteen_id=canteen_b4.id, category_id=cat_drink.id, image_url="https://images.unsplash.com/photo-1511920170033-f8396924c348?w=400&h=300&fit=crop")
            
            db.session.add_all([food1, food2, drink1])
            db.session.commit()
            print("Nạp dữ liệu mẫu THÀNH CÔNG!")
        else:
            print("Dữ liệu đã tồn tại.")

if __name__ == '__main__':
    seed_database()