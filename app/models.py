from app import db


# User Table - info about users
class User(db.Model):

    id = db.Column(db.Integer,primary_key = True)
    name = db.Column(db.String(128),nullable=False)
    email = db.Column(db.String(256),unique=True,nullable=False)
    password = db.Column(db.String(128),nullable=False)
    is_admin = db.Column(db.Boolean,default=False)
    borrow_requests = db.relationship('BorrowRequest',backref='user',lazy=True)
    borrow_history = db.relationship('BorrowHistory',backref='user',lazy=True)

#Book Table - Info about books 
class Book(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(128),nullable=False)
    author = db.Column(db.String(256),nullable=False)
    quantity = db.Column(db.Integer, default=1)

# Borrowrequest Table - Info about request about particular book
class BorrowRequest(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    book_id = db.Column(db.Integer,db.ForeignKey('book.id'),nullable=False)
    start_date = db.Column(db.DateTime,nullable=False)
    end_date = db.Column(db.DateTime,nullable=False)
    status = db.Column(db.String(128),default='Pending')


    @staticmethod
    def is_book_available(book_id, start_date, end_date):
        book = Book.query.get(book_id)
        if book is None or book.quantity is None or book.quantity == 0:
            return False
        conflicting_request = BorrowRequest.query.filter(
            BorrowRequest.book_id == book_id,  BorrowRequest.status == 'Approved',  
            BorrowRequest.start_date < end_date, BorrowRequest.end_date > start_date).first()
        if conflicting_request:
            return False
        return True



#BorrowHistory - info about borrow history
class BorrowHistory(db.Model):

    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    book_id = db.Column(db.Integer,db.ForeignKey('book.id'),nullable=False)
    start_date = db.Column(db.DateTime,nullable=False)
    end_date = db.Column(db.DateTime,nullable=False) 