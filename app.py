"""
產品驗證查詢系統 - 後端 API
使用 Flask + SQLite
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os
from datetime import datetime

app = Flask(__name__, static_folder='static')
CORS(app)

DATABASE = 'products.db'

def get_db():
    """取得資料庫連線"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化資料庫"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 建立產品資料表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_code TEXT UNIQUE NOT NULL,
            product_name TEXT NOT NULL,
            hospital_name TEXT NOT NULL,
            purchase_date DATE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 建立索引以加速查詢
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_product_code ON products(product_code)
    ''')
    
    conn.commit()
    conn.close()
    print("資料庫初始化完成")

# ==================== 前台 API ====================

@app.route('/')
def index():
    """前台查詢頁面"""
    return send_from_directory('static', 'index.html')

@app.route('/admin')
def admin():
    """後台管理頁面"""
    return send_from_directory('static', 'admin.html')

@app.route('/api/verify/<product_code>', methods=['GET'])
def verify_product(product_code):
    """
    驗證產品編碼
    GET /api/verify/{product_code}
    """
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT product_code, product_name, hospital_name, purchase_date 
        FROM products 
        WHERE UPPER(product_code) = UPPER(?)
    ''', (product_code,))
    
    product = cursor.fetchone()
    conn.close()
    
    if product:
        return jsonify({
            'success': True,
            'verified': True,
            'data': {
                'product_code': product['product_code'],
                'product_name': product['product_name'],
                'hospital_name': product['hospital_name'],
                'purchase_date': product['purchase_date']
            }
        })
    else:
        return jsonify({
            'success': True,
            'verified': False,
            'message': '查無此產品編碼，請確認編碼是否正確'
        })

# ==================== 後台 API ====================

@app.route('/api/products', methods=['GET'])
def get_all_products():
    """
    取得所有產品（支援分頁）
    GET /api/products?page=1&per_page=20&search=關鍵字
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '', type=str)
    
    conn = get_db()
    cursor = conn.cursor()
    
    offset = (page - 1) * per_page
    
    if search:
        # 搜尋產品編碼、名稱或醫院
        search_pattern = f'%{search}%'
        cursor.execute('''
            SELECT COUNT(*) FROM products 
            WHERE product_code LIKE ? OR product_name LIKE ? OR hospital_name LIKE ?
        ''', (search_pattern, search_pattern, search_pattern))
        total = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT * FROM products 
            WHERE product_code LIKE ? OR product_name LIKE ? OR hospital_name LIKE ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (search_pattern, search_pattern, search_pattern, per_page, offset))
    else:
        cursor.execute('SELECT COUNT(*) FROM products')
        total = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT * FROM products 
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (per_page, offset))
    
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({
        'success': True,
        'data': products,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': (total + per_page - 1) // per_page
        }
    })

@app.route('/api/products', methods=['POST'])
def add_product():
    """
    新增產品
    POST /api/products
    Body: { product_code, product_name, hospital_name, purchase_date }
    """
    data = request.get_json()
    
    required_fields = ['product_code', 'product_name', 'hospital_name', 'purchase_date']
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                'success': False,
                'message': f'缺少必要欄位: {field}'
            }), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO products (product_code, product_name, hospital_name, purchase_date)
            VALUES (?, ?, ?, ?)
        ''', (
            data['product_code'].upper(),
            data['product_name'],
            data['hospital_name'],
            data['purchase_date']
        ))
        conn.commit()
        product_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '產品新增成功',
            'id': product_id
        }), 201
        
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({
            'success': False,
            'message': '產品編碼已存在'
        }), 409

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """
    更新產品
    PUT /api/products/{id}
    """
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 檢查產品是否存在
    cursor.execute('SELECT id FROM products WHERE id = ?', (product_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({
            'success': False,
            'message': '找不到該產品'
        }), 404
    
    # 檢查新編碼是否與其他產品重複
    if data.get('product_code'):
        cursor.execute('''
            SELECT id FROM products 
            WHERE UPPER(product_code) = UPPER(?) AND id != ?
        ''', (data['product_code'], product_id))
        if cursor.fetchone():
            conn.close()
            return jsonify({
                'success': False,
                'message': '產品編碼已被其他產品使用'
            }), 409
    
    # 更新資料
    update_fields = []
    update_values = []
    
    if data.get('product_code'):
        update_fields.append('product_code = ?')
        update_values.append(data['product_code'].upper())
    if data.get('product_name'):
        update_fields.append('product_name = ?')
        update_values.append(data['product_name'])
    if data.get('hospital_name'):
        update_fields.append('hospital_name = ?')
        update_values.append(data['hospital_name'])
    if data.get('purchase_date'):
        update_fields.append('purchase_date = ?')
        update_values.append(data['purchase_date'])
    
    update_fields.append('updated_at = ?')
    update_values.append(datetime.now().isoformat())
    update_values.append(product_id)
    
    cursor.execute(f'''
        UPDATE products 
        SET {', '.join(update_fields)}
        WHERE id = ?
    ''', update_values)
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': '產品更新成功'
    })

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """
    刪除產品
    DELETE /api/products/{id}
    """
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM products WHERE id = ?', (product_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({
            'success': False,
            'message': '找不到該產品'
        }), 404
    
    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': '產品刪除成功'
    })

@app.route('/api/products/batch', methods=['POST'])
def batch_add_products():
    """
    批次新增產品
    POST /api/products/batch
    Body: { products: [{ product_code, product_name, hospital_name, purchase_date }, ...] }
    """
    data = request.get_json()
    products = data.get('products', [])
    
    if not products:
        return jsonify({
            'success': False,
            'message': '沒有提供產品資料'
        }), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    success_count = 0
    errors = []
    
    for i, product in enumerate(products):
        try:
            cursor.execute('''
                INSERT INTO products (product_code, product_name, hospital_name, purchase_date)
                VALUES (?, ?, ?, ?)
            ''', (
                product['product_code'].upper(),
                product['product_name'],
                product['hospital_name'],
                product['purchase_date']
            ))
            success_count += 1
        except sqlite3.IntegrityError:
            errors.append(f"第 {i+1} 筆: 編碼 {product['product_code']} 已存在")
        except KeyError as e:
            errors.append(f"第 {i+1} 筆: 缺少欄位 {e}")
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': f'成功新增 {success_count} 筆，失敗 {len(errors)} 筆',
        'success_count': success_count,
        'errors': errors
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """取得統計資料"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM products')
    total = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(DISTINCT hospital_name) FROM products
    ''')
    hospital_count = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'success': True,
        'data': {
            'total_products': total,
            'total_hospitals': hospital_count
        }
    })

# 確保 static 資料夾存在
os.makedirs('static', exist_ok=True)

# 初始化資料庫（部署時也會執行）
init_db()

if __name__ == '__main__':
    # 啟動伺服器
    print("伺服器啟動中...")
    print("前台查詢頁面: http://localhost:5000")
    print("後台管理頁面: http://localhost:5000/admin")
    app.run(host='0.0.0.0', port=5000, debug=True)
