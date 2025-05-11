from django.urls import path
from .views import *
urlpatterns = [
    # ----------------------------------------------------------------------------------------------------------------------------------------------
    #                                                       AUTHENTICATION URLS
    # ----------------------------------------------------------------------------------------------------------------------------------------------
    path('', Login, name='lib-login'),
    path('librarian/logout/', Logout, name='logout'),

    # ----------------------------------------------------------------------------------------------------------------------------------------------
    #                                                       DASHBOARD URLS
    # ----------------------------------------------------------------------------------------------------------------------------------------------
    path('home', Dashboard, name='lib-dashboard'),

    # ----------------------------------------------------------------------------------------------------------------------------------------------
    #                                                       BOOKS URLS
    # ----------------------------------------------------------------------------------------------------------------------------------------------
    path('books', Books, name='lib-book-list'),
    path('books/edit/<int:book_id>/', EditBook, name='lib-book-edit'),
    path('books/delete/<int:book_id>/', DeleteBook, name='lib-delete-book'),
    path('books/history/<int:book_id>/', BookHistory, name='lib-book-view'),
    path('books/new', NewBook, name='lib-new-book'),

    # ----------------------------------------------------------------------------------------------------------------------------------------------
    #                                                       BORROW URLS
    # ----------------------------------------------------------------------------------------------------------------------------------------------
    path('borrowing',NewBorrow, name='lib-borrow'),
    path('books/borrowed',BorrowedBooks, name='lib-books-borrowed'),
    path('return-book/<int:borrow_id>/', ReturnBook, name='lib-return-book'),
    path('return-book/fine/<int:borrow_id>/', ReturnBookWithFine, name='lib-return-book-with-fine'),

    # ----------------------------------------------------------------------------------------------------------------------------------------------
    #                                                       SHELVES URLS
    # ----------------------------------------------------------------------------------------------------------------------------------------------
    path('shelves', Shelves, name='shelves'),
    path('shelves/new', NewShelf, name='new-shelf'),
    path('shelves/edit/<int:shelf_id>/', EditShelf, name='edit-shelf'),
    path('shelves/delete/<int:shelf_id>/', DeleteShelf, name='delete-shelf'),

    # ----------------------------------------------------------------------------------------------------------------------------------------------
    #                                                       BILLING URLS
    # ----------------------------------------------------------------------------------------------------------------------------------------------
    path('billing', Billing, name='lib-billing'),
    path('billing-pdf/<int:student_id>/', billing_pdf, name='billing_pdf'),

    # ----------------------------------------------------------------------------------------------------------------------------------------------
    #                                                       STUDENTS URLS
    # ----------------------------------------------------------------------------------------------------------------------------------------------
    path('students', Students, name='lib-student-list' ),
    path('students/new', NewStudent, name='lib-new-student'),
    path('students/<str:student_id>/', UpdateStudent, name='lib-update-student'),
    path('student/<str:student_id>/', SingleStudent, name='lib-single-student'),
    path('student/delete/<str:student_id>/', DeleteStudent, name='lib-delete-student'),

    # ----------------------------------------------------------------------------------------------------------------------------------------------
    #                                                       SUBJECTS URLS
    # ----------------------------------------------------------------------------------------------------------------------------------------------
    path('subjects', Subjects, name='subjects'),
    path('subjects/new', NewSubject, name='new-subject'),

    # ----------------------------------------------------------------------------------------------------------------------------------------------
    #                                                       FINES URLS
    # ----------------------------------------------------------------------------------------------------------------------------------------------
    path('fines', FineList, name='lib-fine-list'),
    path('fines/detail/<str:fine_id>/', fine_detail, name='lib-fine-detail'),
    path('fines/pay/<str:fine_id>/', PayFine, name='lib-pay-fine'),
]