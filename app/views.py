from flask import request,jsonify, make_response
from app import app,db
from .models import User,Book,BorrowHistory,BorrowRequest
from werkzeug.security import generate_password_hash
from sqlalchemy import or_,and_
from datetime import datetime
from flask_jwt_extended import create_access_token, create_refresh_token,jwt_required, get_jwt_identity
import csv

# API1 - Create a New Librarian
@app.route("/library/create_admin",methods=['POST'])
def create_admin():

    data = request.json
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    is_admin = data.get("is_admin", False)
    # Check for required fields
    required_fields = ['email', 'password']
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        missing = ", ".join(missing_fields)
        return jsonify({'error': f'{missing} is required'}), 400
    hash_pass = generate_password_hash(password)
    if User.query.filter_by(email=email).first():
        return jsonify({"Error":"Email already exists"}),400
    user = User(name=name, email=email, password=hash_pass, is_admin=is_admin)
    access_token = create_access_token(identity=email)
    refresh_token = create_refresh_token(identity=email)
    db.session.add(user)
    db.session.commit()
    if is_admin:
        access_token = create_access_token(identity=email)
        refresh_token = create_refresh_token(identity=email)
        return jsonify({
            'message': 'Admin user created successfully',
            'access_token': access_token,
            'refresh_token': refresh_token
        }), 201

    return jsonify({'message': 'User created successfully'}), 201



# API2 - View All Borrow Requests
@app.route("/borrow_requests/all", methods=['GET'])
@jwt_required()
def borrow_req():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    requests = BorrowRequest.query.paginate(page=page, per_page=per_page)
    
    current_user = get_jwt_identity()
    user = User.query.filter_by(email=current_user).first()
    if not user or not user.is_admin:
        return jsonify({"error": "Access forbidden: Admin privileges required."}), 403

    results = [
        {
            "user_id": req.user_id,
            "book_id": req.book_id,
            "start_date": req.start_date,
            "end_date": req.end_date,
            "status": req.status
        }
        for req in requests.items
    ]
    
    return jsonify({
        "Requests": results,
        "total": requests.total,
        "pages": requests.pages,
        "current_page": requests.page,
        "per_page": requests.per_page
    }), 200

        
#API3  - approve/deny the request
@app.route('/borrow_request/check_and_approve/<int:request_id>', methods=['PUT'])
@jwt_required()
def check_and_approve_borrow_request(request_id):
    current_user = get_jwt_identity()
    user = User.query.filter_by(email=current_user).first()
    if not user or not user.is_admin:
        return jsonify({"error": "Access forbidden: Admin privileges required."}), 403
    
    borrow_request = BorrowRequest.query.get(request_id)
    if not borrow_request:
        return jsonify({'error': 'Borrow request not found.'}), 404

    if borrow_request.status == 'Approved':
        return jsonify({'error': 'This borrow request has already been approved'}), 400

    # First, check if the book is available (i.e., has quantity)
    book = Book.query.get(borrow_request.book_id)
    if not book or book.quantity <= 0:
        borrow_request.status = 'Denied'
        db.session.commit()
        return jsonify({'message': 'Borrow request denied.', 'error': 'Book is not available.'}), 400
    
    # Next, check if the book is available during the requested time slot
    is_available = BorrowRequest.is_book_available(borrow_request.book_id, borrow_request.start_date, borrow_request.end_date)
    if not is_available:
        borrow_request.status = 'Denied'
        db.session.commit()
        return jsonify({'message': 'Borrow request denied.', 'error': 'Book is not available for the selected period.'}), 400

    # If both checks pass, approve the borrow request and reduce the book quantity
    book.quantity -= 1
    db.session.commit()

    borrow_request.status = 'Approved'
    db.session.commit()

    # Create the borrow history record
    borrow_history = BorrowHistory(
        user_id=borrow_request.user_id,
        book_id=borrow_request.book_id,
        start_date=borrow_request.start_date,
        end_date=borrow_request.end_date
    )
    db.session.add(borrow_history)
    db.session.commit()

    return jsonify({'message': 'Borrow request approved successfully.'}), 200



# API4 - View a User’s Borrow History 
@app.route("/user/borrow_history/<int:user_id>",methods=['GET'])
@jwt_required()
def user_borrow_history(user_id):
    current_user = get_jwt_identity()
    user = User.query.filter_by(email=current_user).first()
    if not user or not user.is_admin:
        return jsonify({"error": "Access forbidden: Admin privileges required."}), 403
    borrow_history = BorrowHistory.query.filter_by(user_id=user_id).all()
    results = [{
        'book_id': history.book_id,
        'start_date': history.start_date,
        'end_date': history.end_date,
        'quantity': Book.query.get(history.book_id).quantity  # Add current quantity here if needed
    } for history in borrow_history]
    return jsonify({"History": results}), 200


# API5 - List all books
@app.route('/all/books', methods=['GET'])
def get_books():
    page = request.args.get('page', 1, type=int)  
    per_page = request.args.get('per_page', 10, type=int)  
    author = request.args.get('author', None)  
    title = request.args.get('title', None)  

    query = Book.query
    if author:
        query = query.filter(Book.author == author)  # Exact match for author
    if title:
        query = query.filter(Book.title == title)  # Exact match for title

    books = query.paginate(page=page, per_page=per_page) 
    results = [{
        'id': book.id, 'title': book.title, 'author': book.author,'quantity':book.quantity
    } for book in books.items]  

    return jsonify({
        "Books": results,
        "total": books.total,
        "pages": books.pages,
        "current_page": books.page,
        "per_page": books.per_page
    }), 200




#API6 - Submit a Request to Borrow a Book
@app.route('/user/borrow_request', methods=['POST'])
def borrow_request():
    data = request.get_json()
    user_id = data.get('user_id')
    book_id = data.get('book_id')
    start_date = datetime.strptime(data.get('start_date'), '%Y-%m-%d').date()
    end_date = datetime.strptime(data.get('end_date'), '%Y-%m-%d').date()

    if not all([user_id, book_id, start_date, end_date]):
        return jsonify({'error': 'Missing required fields.'}), 400
    if start_date > end_date:
        return jsonify({'error': 'Start date cannot be after end date.'}), 400
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found.'}), 404
    book = Book.query.get(book_id)
    if not book:
        return jsonify({'error': 'Book not found.'}), 404
    if not BorrowRequest.is_book_available(book_id, start_date, end_date):
        return jsonify({'error': 'Book is already borrowed for the selected period.'}), 400
    borrow_request = BorrowRequest(user_id=user_id, book_id=book_id, 
                                   start_date=start_date, end_date=end_date)
    db.session.add(borrow_request)
    db.session.commit()
    return jsonify({'message': 'Borrow request submitted successfully.'}), 201


#API7 - User's Borrow History
@app.route("/book/borrow_history/<int:book_id>",methods=['GET'])
def book_borrow_history(book_id):
    borrow_history = BorrowHistory.query.filter_by(book_id=book_id).all()
    results = [{
        'user_id': history.user_id,
        'start_date': history.start_date,
        'end_date': history.end_date
    } for history in borrow_history]
    return jsonify({"History":results}), 200



# API8 - Get all borrow requests made by users
@app.route('/librarian/borrow_requests', methods=['GET'])
def get_borrow_requests():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    requests = BorrowRequest.query.paginate(page=page, per_page=per_page)
    results = [
        {
            "user_id": req.user_id,
            "book_id": req.book_id,
            "start_date": req.start_date,
            "end_date": req.end_date,
            "status": req.status
        }
        for req in requests.items
    ]
    
    return jsonify({
        "Requests": results,
        "total": requests.total,
        "pages": requests.pages,
        "current_page": requests.page,
        "per_page": requests.per_page
    }), 200



# API9 - create_book
@app.route('/librarian/add_book', methods=['POST'])
@jwt_required()
def add_book():
    data = request.get_json()
    title = data.get('title')
    author = data.get('author')
    quantity = data.get('quantity', 1)  
    if not title or not author:
        return jsonify({'error': 'Both title and author are required'}), 400
    existing_book = Book.query.filter_by(title=title, author=author).first()
    if existing_book:
        existing_book.quantity += quantity  
        db.session.commit()
        return jsonify({'message': 'Book already exists, quantity updated.', 'book': {'id': existing_book.id, 'title': existing_book.title, 'author': existing_book.author, 'quantity': existing_book.quantity}}), 200
    new_book = Book(title=title, author=author, quantity=quantity)
    db.session.add(new_book)
    db.session.commit()
    return jsonify({'message': 'Book added successfully!', 'book': {'id': new_book.id, 'title': new_book.title, 'author': new_book.author, 'quantity': new_book.quantity}}), 201


# API 10 - Handling Book Return
@app.route("/user/return_book/<int:borrow_history_id>", methods=['PUT'])
def return_book(borrow_history_id):
    data = request.json
    user_email = data.get('email')
    if not user_email:
        return jsonify({'error': 'User email is required to return a book.'}), 400
    user = User.query.filter_by(email=user_email).first()
    if not user:
        return jsonify({'error': 'User not found.'}), 404
    borrow_history = BorrowHistory.query.get(borrow_history_id)
    if not borrow_history:
        return jsonify({'error': 'Borrow history record not found.'}), 404
    if borrow_history.user_id != user.id:
        return jsonify({'error': 'You are not authorized to return this book.'}), 403
    book = Book.query.get(borrow_history.book_id)
    if book:
        book.quantity += 1
        db.session.commit()
    db.session.delete(borrow_history)
    db.session.commit()
    return jsonify({'message': 'Book returned successfully.'}), 200



# API11 - refersh token

@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)  # Requires a refresh token
def refresh():
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)
    return jsonify({
        "access_token": new_access_token
    }), 200



# API12 - Download Borrow History as CSV
@app.route("/user/borrow_history/download", methods=['GET'])
@jwt_required()
def download_borrow_history():
    current_user_id = get_jwt_identity() 
    user = User.query.filter_by(email=current_user_id).first()
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    borrow_history = BorrowRequest.query.filter_by(user_id=current_user_id).all()
    if not borrow_history:
        return jsonify({'error': 'No borrow history found for this user.'}), 404

    # Create an in-memory CSV file
    from io import StringIO
    csv_file = StringIO()
    writer = csv.writer(csv_file)
    writer.writerow(['Book Title', 'Author', 'Start Date', 'End Date', 'Status'])

    # Write the borrow history to the CSV
    for request in borrow_history:
        book = Book.query.get(request.book_id)
        writer.writerow([
            book.title if book else 'Unknown',
            book.author if book else 'Unknown',
            request.start_date,
            request.end_date,
            request.status
        ])

    # Generate response to download the CSV file
    response = make_response(csv_file.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=borrow_history_user_{current_user_id}.csv'
    response.headers['Content-Type'] = 'text/csv'
    csv_file.close()

    return response