from django.shortcuts import render,  redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from base.models import *
from django.db.models import Q
from django.db.models import Sum
from django.db.models import Count
from datetime import date
from django.db.models import F, Value, Case, When, BooleanField
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import *
from weasyprint import HTML
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.timezone import now
# Create your views here.


# ----------------------------------------------------------------------------------------------------------------------------------------------
#                                                       AUTHENTICATION VIEWS
# ----------------------------------------------------------------------------------------------------------------------------------------------

def Login(request):
    if request.method == "POST":
        username = request.POST.get("username")  # Get username from the input name
        password = request.POST.get("password")  # Get password from the input name
        
        user = authenticate(request, username=username, password=password)  # Authenticate user
        if user is not None:
            if user.groups.filter(name='Librarians').exists():  # Check if the user is in the 'Librarians' group
                login(request, user)
                return redirect('lib-dashboard')  # Redirect to dashboard
            else:
                messages.error(request, "You do not have the required permissions to access this system.")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'Librarian/sign-in.html')

def Logout(request):
    logout(request)
    return redirect('lib-login')  


# ----------------------------------------------------------------------------------------------------------------------------------------------
#                                                       END AUTHENTICATION VIEWS
# ----------------------------------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------------------------------
#                                                       DASHBOARD VIEWS
# ----------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='lib-login')
def Dashboard(request):
    total_books = Book.objects.all().count()
    total_users = Student.objects.all().count()
    total_books_borrowed = Borrow.objects.filter(status='borrowed').count()
    total_penalty = Fine.objects.aggregate(total_fine=Sum('amount'))['total_fine'] or 0

    books = Book.objects.values('subject__name').annotate(subject_count=Count('subject'))
   # Fetch books and their statuses
    books_statuses = Borrow.objects.annotate(
        book_title=F('book__title'),  # Get the book title
        current_status=F('status'),  # Get the borrow status
        book_due_date=F('due_date'),  # Due date for borrowing
        overdue=Case(
            When(due_date__lt=date.today(), then=Value(True)),  # Overdue if due_date < today
            default=Value(False),
            output_field=BooleanField()
        )
    ).values('book_title', 'current_status', 'book_due_date', 'overdue').order_by('borrow_date')

    # Set up pagination with 10 items per page
    paginator = Paginator(books, 10)  # Show 10 shelves per page
    page_number = request.GET.get('page')  # Get the page number from the URL query parameters
    page_obj = paginator.get_page(page_number)  # Get the page object
    
    context = {
        'title':'Dashboard',
        'total_books':total_books,
        'users':total_users,
        'books_borrowed':total_books_borrowed,
        'penalty':total_penalty,
        'books':books,
        'books': page_obj,
        'books_statuses': books_statuses,
    }
    return render(request, 'Librarian/dashboard.html', context)


# ----------------------------------------------------------------------------------------------------------------------------------------------
#                                                       END DASHBOARD VIEWS
# ----------------------------------------------------------------------------------------------------------------------------------------------



# ----------------------------------------------------------------------------------------------------------------------------------------------
#                                                       SHELVES VIEWS
# ----------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='lib-login')
def Shelves(request):
    # Get search and filter parameters from the request
    q = request.GET.get('q', '')  # Search by name
    space_filter = request.GET.get('space_filter', 'all')  # Filter for available space

    # Base query for shelves
    shelves = Shelf.objects.filter(
        Q(name__icontains=q)
    ).annotate(
        book_count=Count('book'),
        space_left=F('capacity') - Count('book')
    )

    # Apply space filter
    if space_filter == 'available':
        shelves = shelves.filter(space_left__gt=0)
    elif space_filter == 'full':
        shelves = shelves.filter(space_left__lte=0)

    # Set up pagination with 10 items per page
    paginator = Paginator(shelves, 10)  # Show 10 shelves per page
    page_number = request.GET.get('page')  # Get the page number from the URL query parameters
    page_obj = paginator.get_page(page_number)  # Get the page object

    context = {
        'title': 'Shelves',
        'shelves': page_obj,  # Pass the paginated shelves to the template
        'current_q': q,  # Preserve the search query in the template
        'current_space_filter': space_filter,  # Preserve the filter value in the template
    }
    return render(request, 'Librarian/shelves.html', context)


@login_required(login_url='lib-login')
def NewShelf(request):
    if request.method == "POST":
        name = request.POST.get("shelf_name")  
        capacity = request.POST.get("shelf_capacity")

        # Validate inputs
        if not name or not capacity:
            messages.error(request, "All fields are required!")
        elif not capacity.isdigit() or int(capacity) <= 0:
            messages.error(request, "Capacity must be a positive number!")
        else:
            # Save the new shelf
            Shelf.objects.create(name=name, capacity=int(capacity))
            messages.success(request, "New shelf added successfully!")
            return redirect('new-shelf')  # Replace 'shelf-list' with the name of your shelf list URL pattern
       
    context = {
        'title':'New Shelf'
    }
    return render(request, 'Librarian/new-shelf.html', context)


@login_required(login_url='lib-login')
def EditShelf(request, shelf_id):
    # Get the shelf object by ID or raise a 404 if not found
    shelf = get_object_or_404(Shelf, id=shelf_id)
    
    if request.method == "POST":
        name = request.POST.get("shelf_name")
        capacity = request.POST.get("shelf_capacity")
        
        # Validate inputs
        if not name or not capacity:
            messages.error(request, "All fields are required!")
        elif not capacity.isdigit() or int(capacity) <= 0:
            messages.error(request, "Capacity must be a positive number!")
        else:
            # Update the shelf details
            shelf.name = name
            shelf.capacity = int(capacity)
            shelf.save()
            messages.success(request, f"{shelf.name} updated successfully!")
            return redirect('shelves')  # Replace 'shelves' with your shelf list URL pattern
    
    context = {
        'title': 'Edit Shelf',
        'shelf': shelf
    }
    return render(request, 'Librarian/edit-shelf.html', context)


@login_required(login_url='lib-login')
def DeleteShelf(request, shelf_id):
    # Get the shelf object by ID or raise a 404 if not found
    shelf = get_object_or_404(Shelf, id=shelf_id)

    # Check if the request method is POST to confirm the deletion
    if request.method == "POST":
        shelf.delete()
        messages.success(request, f"{shelf.name} deleted successfully!")
        return redirect('shelves')  # Redirect to the shelves list page

    context = {
        'title': 'Delete Shelf',
        'shelf': shelf
    }
    return render(request, 'Librarian/confirm-delete-shelf.html', context)


# ----------------------------------------------------------------------------------------------------------------------------------------------
#                                                       END SHELVES VIEWS
# ----------------------------------------------------------------------------------------------------------------------------------------------



# ----------------------------------------------------------------------------------------------------------------------------------------------
#                                                       BORROW VIEWS
# ----------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='lib-login')
def NewBorrow(request):
    books_exist = Book.objects.exists()
    if request.method == 'POST':
        student_id = request.POST.get("student_id")
        book_isbn = request.POST.get("book_isbn")
        due_date = request.POST.get("due_date")

        # Validate inputs
        if not student_id or not book_isbn:
            messages.error(request, "Student and Book are required!")
            return redirect('lib-new-borrow')

        try:
            student = Student.objects.get(id=student_id)
            book = Book.objects.get(isbn=book_isbn)

            # Check if the book is already borrowed
            if Borrow.objects.filter(book=book, status='borrowed').exists():
                messages.error(request, f"Book '{book.title}' is already borrowed!")
                return redirect('lib-new-borrow')

            # If due_date is not provided, calculate it
            if not due_date:
                due_date = date.today() + timedelta(days=14)  # Default due date is 14 days from today
            else:
                due_date = date.fromisoformat(due_date)  # Parse the given date string

            # Create a new Borrow record
            borrow = Borrow(
                student=student,
                book=book,
                due_date=due_date
            )
            borrow.save()

            messages.success(request, f"Book '{book.title}' borrowed successfully!")
            return redirect('lib-books-borrowed')  # Redirect to a list of books or other relevant page

        except Student.DoesNotExist:
            messages.error(request, "Invalid student selected!")
        except Book.DoesNotExist:
            messages.error(request, "Invalid book selected!")
        except ValueError:
            messages.error(request, "Invalid date format for due date!")

    # Get all students and books that are not borrowed
    students = Student.objects.all()
    books = Book.objects.exclude(borrows__status='borrowed').distinct()  # Books not currently borrowed

    context = {
        'title': 'Borrowing Book',
        'students': students,
        'books': books,
        'books_exist': books_exist
    }
    return render(request, 'Librarian/books-borrow.html', context)


@login_required(login_url='lib-login')
def BorrowedBooks(request):
    books_exist = Book.objects.exists()
    q = request.GET.get('q', '').strip()
    subject_query = request.GET.get('subject', '').strip()

    # Filter records based on student ID and subject
    record = Borrow.objects.filter(
        Q(student__student_id__icontains=q) &
        (Q(book__subject__name__icontains=subject_query) if subject_query else Q()),
    ).order_by('return_date')

    # Set up pagination with 10 items per page
    paginator = Paginator(record, 10)  # Show 10 books per page
    page_number = request.GET.get('page')  # Get the page number from the URL query parameters
    page_obj = paginator.get_page(page_number)  # Get the page object

    # Get all subjects for the filter dropdown
    subjects = Subject.objects.all()
    total = Borrow.objects.filter(status='borrowed').count()
    context = {
        'title': 'Borrowed Books',
        'borrows': page_obj,
        'subjects': subjects,  # Pass subjects to the template
        'total' : total,
        'books_exist': books_exist
    }
    return render(request, 'Librarian/books-borrowed.html', context)


@login_required(login_url='lib-login')
def ReturnBook(request, borrow_id):
    borrow = Borrow.objects.get(id=borrow_id)
    if borrow.status == 'borrowed':
        borrow.status = 'returned'
        borrow.return_date = date.today()
        borrow.save()
        messages.success(request, 'Book has been returned successfully.')
    else:
        messages.error(request, 'This book has already been returned.')

    return redirect('lib-books-borrowed')  # Adjust to your appropriate URL pattern

@login_required(login_url='lib-login')
def ReturnBookWithFine(request, borrow_id):
    borrow = get_object_or_404(Borrow, id=borrow_id)
    fine_form = FineSelectionForm(request.POST or None)

    # Check if the book is borrowed or already returned
    if borrow.status == 'returned':
        messages.error(request, 'This book has already been returned.')
        return redirect('lib-books-borrowed')

    if request.method == 'POST' and fine_form.is_valid():
        fine_type = fine_form.cleaned_data['fine_type']

        # Calculate the fine based on the borrow status
        fine_amount, fine_reason = borrow.calculate_fine()

        # Ensure a valid reason is provided
        if not fine_reason:
            fine_reason = "No reason specified"

        # Update the borrow status and return date based on the fine type
        if fine_type == 'overdue':
            borrow.status = 'returned'
            borrow.return_date = date.today()
        
        elif fine_type == 'lost':
            borrow.status = 'lost'
            borrow.return_date = date.today()

        elif fine_type == 'damaged':
            borrow.status = 'damaged'
            borrow.return_date = date.today()

        # Save the borrow object with updated status and return date
        borrow.save()

        # Check if a fine record exists for the borrow
        fine = Fine.objects.filter(borrow=borrow, reason=fine_reason).first()

        if fine:
            # Update the fine amount and status if the fine already exists
            fine.amount = fine_amount
            fine.status = 'unpaid'  # Mark the fine as unpaid when updating
            fine.save()
        else:
            # If no fine exists, create a new one
            Fine.objects.create(
                borrow=borrow,
                amount=fine_amount,
                reason=fine_reason,
                status='unpaid'
            )

        messages.success(request, f'Book has been returned and {fine_type} fine applied successfully.')
        return redirect('lib-books-borrowed')

    return render(request, 'Librarian/return_book.html', {
        'borrow': borrow,
        'fine_form': fine_form,
    })

# ----------------------------------------------------------------------------------------------------------------------------------------------
#                                                       END BORROW VIEWS
# ----------------------------------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------------------------------
#                                                       BOOK VIEWS
# ----------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='lib-login')
def Books(request):
    # Get query parameters
    q = request.GET.get('q', '').strip()
    subject_id = request.GET.get('subject', '').strip()

    # Base queryset
    books = Book.objects.all().order_by('subject__name')
    books_exist = Book.objects.exists()

    # Apply filters
    if q:
        books = books.filter(Q(title__icontains=q))
    if subject_id:
        books = books.filter(subject_id=subject_id)

    # Annotate with borrowed status
    for book in books:
        book.is_borrowed = Borrow.objects.filter(book=book, status='borrowed').exists()

    # Set up pagination
    paginator = Paginator(books, 10)  # 10 books per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get all subjects for the select dropdown
    subjects = Subject.objects.all().order_by('name')

    context = {
        'title': 'Books',
        'books': page_obj,
        'books_exist': books_exist,
        'subjects': subjects,  # Pass subjects for the dropdown
    }
    return render(request, 'Librarian/books-list.html', context)


@login_required(login_url='li-login')
def BookHistory(request, book_id):
    # Get the book object by ID or raise a 404 if not found
    book = get_object_or_404(Book, id=book_id)  # Correct the model to 'Book'
    
    # Check if the book is borrowed
    book.is_borrowed = Borrow.objects.filter(book=book, status='borrowed').exists()

    # Fetch the history of the book (all borrow records)
    book_history = Borrow.objects.filter(book=book).order_by('-borrow_date')  # Adjust based on your model's fields

     # Set up pagination
    paginator = Paginator(book_history, 10)  # Show 10 borrow records per page
    page = request.GET.get('page')  # Get the current page from the query parameter
    try:
        book_history_paginated = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver the first page
        book_history_paginated = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver the last page of results
        book_history_paginated = paginator.page(paginator.num_pages)
    
    context = {
        'title': 'Book History',
        'book': book,
        'book_history': book_history_paginated  # Pass the borrow history to the template
    }
    
    return render(request, 'Librarian/books-view.html', context)


@login_required(login_url='lib-login')
def NewBook(request):
    subjects_exist = Subject.objects.exists()
    if request.method == 'POST':
        isbn = request.POST.get('isbn')
        title = request.POST.get('title')
        subject_id = request.POST.get('subject')
        shelf_id = request.POST.get('shelf')
        form = request.POST.get('form')
        price = request.POST.get('price')

        # Validate inputs
        if not isbn or not title or not subject_id or not shelf_id or not form or not price:
            messages.error(request, "All fields are required!")
            return redirect('lib-new-book')  # Redirect back to the same page

        try:
            subject = Subject.objects.get(id=subject_id)
            shelf = Shelf.objects.get(id=shelf_id)

            if shelf.current_load() >= shelf.capacity:
                messages.error(request, f"The shelf '{shelf.name}' is full. Please choose another shelf.")
                return redirect('lib-new-book')

            # Check if the shelf is full through the model's save method
            book = Book(isbn=isbn, title=title, subject=subject, shelf=shelf, form=form, price=price)
            book.save()  # This will trigger the save method which checks shelf capacity

            messages.success(request, f"Book '{title}' added successfully!")

            return redirect('lib-new-book')  # Redirect to a list of books page (you may adjust this as needed)

        except Shelf.DoesNotExist:
            messages.error(request, "Invalid shelf selected!")
        except Subject.DoesNotExist:
            messages.error(request, "Invalid subject selected!")
        except ValueError as e:
            messages.error(request, str(e))  # Catch and display the error from the save method

    # For GET request, pass shelves and subjects to the context
    shelves = Shelf.objects.all()
    subjects = Subject.objects.all()

    context = {
        'title': 'New Book',
        'shelves': shelves,
        'subjects': subjects,
        'subjects_exist': subjects_exist,
        'book_form_choices': Book.BOOK_FORM_CHOICES,  # Pass the form choices here
    }
    return render(request, 'Librarian/books-new.html', context)


@login_required(login_url='lib-login')
def EditBook(request, book_id):
    # Fetch the book object by ID or return a 404 error if not found
    book = get_object_or_404(Book, id=book_id)

    if request.method == 'POST':
        isbn = request.POST.get('isbn')
        title = request.POST.get('title')
        subject_id = request.POST.get('subject')
        shelf_id = request.POST.get('shelf')
        form = request.POST.get('form')

        # Validate inputs
        if not isbn or not title or not subject_id or not shelf_id or not form:
            messages.error(request, "All fields are required!")
            return redirect('lib-edit-book', book_id=book.id)  # Redirect back to the edit page

        try:
            # Fetch the subject and shelf objects
            subject = Subject.objects.get(id=subject_id)
            shelf = Shelf.objects.get(id=shelf_id)

            # Update the book object with the new values
            book.isbn = isbn
            book.title = title
            book.subject = subject
            book.shelf = shelf
            book.form = form

            # Check if the shelf is full through the model's save method
            book.save()  # This will trigger the save method which checks shelf capacity

            messages.success(request, f"Book '{title}' updated successfully!")

            return redirect('lib-book-list')  # Redirect to the book list page after update

        except Shelf.DoesNotExist:
            messages.error(request, "Invalid shelf selected!")
        except Subject.DoesNotExist:
            messages.error(request, "Invalid subject selected!")
        except ValueError as e:
            messages.error(request, str(e))  # Catch and display the error from the save method

    # For GET request, pass shelves, subjects, and the current book object to the context
    shelves = Shelf.objects.all()
    subjects = Subject.objects.all()

    context = {
        'title': 'Edit Book',
        'shelves': shelves,
        'subjects': subjects,
        'book': book,  # Pass the book object to prepopulate the form
        'book_form_choices': Book.BOOK_FORM_CHOICES,  # Pass the form choices here
    }
    return render(request, 'Librarian/books-edit.html', context)



@login_required(login_url='lib-login')
def DeleteBook(request, book_id):
    # Get the book object by ID or raise a 404 if not found
    book = get_object_or_404(Book, id=book_id)

    # Check if the request method is POST to confirm the deletion
    if request.method == "POST":
        book.delete()
        messages.success(request, "Book deleted successfully!")
        return redirect('lib-book-list')  # Redirect to the books list page

    context = {
        'title': 'Delete Book',
        'book': book
    }
    return render(request, 'Librarian/confirm-delete-book.html', context)


@login_required(login_url='lib-login')
def Billing(request):
    # Get search query for student_id and filter query for status
    student_id_query = request.GET.get('student_id', '')
    status_query = request.GET.get('status', '')

    # Start with all borrowed, returned, lost, or damaged books with fines greater than 0
    books = Borrow.objects.filter(fine__gt=0, status__in=['borrowed', 'returned', 'lost', 'damaged'])

    # Apply search filter for student_id if provided
    if student_id_query:
        books = books.filter(student__id__icontains=student_id_query)

    # Apply status filter if provided
    if status_query:
        books = books.filter(status=status_query)

    # Set up pagination with 10 books per page
    paginator = Paginator(books, 10)  # Show 10 books per page
    page_number = request.GET.get('page')  # Get the page number from the URL query parameters
    page_obj = paginator.get_page(page_number)  # Get the page object

    context = {
        'title': 'Books with Fines',
        'borrowed_books': page_obj,  # Pass the page object to the template
        'student_id_query': student_id_query,
        'status_query': status_query,
    }
    return render(request, 'Librarian/billing.html', context)


def billing_pdf(request, student_id):
    # Fetch the student's borrowed books and fines
    student = get_object_or_404(Student, pk=student_id)
    borrowed_books = Borrow.objects.filter(student=student)
    subtotal = sum(borrow.fine for borrow in borrowed_books)

     # System name
    system_name = "Library Management System"

    # Prepare the context for rendering the PDF template
    context = {
        'borrowed_books': borrowed_books,
        'student': student,
        'subtotal': subtotal,
        'system_name':system_name,
        'now': now(),
    }

    # Render the HTML template to a string
    html_content = render_to_string('Librarian/billing_pdf.html', context)

    # Generate PDF from HTML
    pdf_file = HTML(string=html_content).write_pdf()

    # Return the PDF response
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="billing_{student.student_id}.pdf"'

    return response

# ----------------------------------------------------------------------------------------------------------------------------------------------
#                                                       END BOOK VIEWS
# ----------------------------------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------------------------------
#                                                       STUDENT VIEWS
# ----------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='lib-login')
def Students(request):
    # Get query parameters
    q = request.GET.get('q', '').strip()
    student_id = request.GET.get('student', '').strip()

    # Base queryset
    students = Student.objects.all().order_by('student_id')

    # Apply filters
    if q:
        students = students.filter(Q(title__icontains=q))
    if student_id:
        students = students.filter(subject_id=student_id)

    # Set up pagination
    paginator = Paginator(students, 10)  # 10 students per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)


    # Get all unique form choices from Student model
    form_choices = Student.STUDENT_FORM_CHOICES

    context = {
        'title': 'Books',
        'books': page_obj,
        'students': students,  # Pass subjects for the dropdown
        'forms':form_choices
    }
    return render(request, 'Librarian/students-list.html', context)


@login_required(login_url='lib-login')
def NewStudent(request):
    if request.method == 'POST':
        # Fetching data from the POST request
        student_id = request.POST.get('student_id')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        form = request.POST.get('form')
        email = request.POST.get('email')
        phone = request.POST.get('phone')

        # Validate inputs: Ensure all fields are provided
        if not student_id or not first_name or not last_name or not form or not email or not phone:
            messages.error(request, "All fields are required!")
            return redirect('lib-new-student')  # Redirect to the same page with an error message

        try:
            # Check if the student with the provided student_id already exists
            existing_student = Student.objects.filter(student_id=student_id).first()
            
            if existing_student:
                messages.error(request, "A student with this ID already exists.")
                return redirect('lib-new-student')

            # Create and save a new student
            student = Student(student_id=student_id, first_name=first_name, last_name=last_name, 
                              email=email, phone=phone, form=form)
            student.save()  # Save the new student

            messages.success(request, f"Student '{first_name} {last_name}' added successfully!")
            return redirect('lib-new-student')  # Redirect to a page with success message

        except Exception as e:
            messages.error(request, f"Error saving student: {str(e)}")  # Catch any errors and display them

    # For GET request, show the form to create a new student
    context = {
        'title': 'New Student',
        'student_form_choices': Student.STUDENT_FORM_CHOICES,  # Pass form choices here if needed
    }
    return render(request, 'Librarian/students-new.html', context)


@login_required(login_url='lib-login')
def UpdateStudent(request, student_id):
    # Fetch the student object based on the student_id
    try:
        student = Student.objects.get(student_id=student_id)
    except Student.DoesNotExist:
        messages.error(request, "Student not found.")
        return redirect('lib-student-list')  # Redirect to the student list if the student doesn't exist

    if request.method == 'POST':
        # Fetching updated data from the POST request
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        form = request.POST.get('form')
        email = request.POST.get('email')
        phone = request.POST.get('phone')

        # Validate inputs: Ensure all fields are provided
        if not first_name or not last_name or not form or not email or not phone:
            messages.error(request, "All fields are required!")
            return redirect('lib-update-student', student_id=student_id)  # Redirect back to the update page

        try:
            # Update the student's data
            student.first_name = first_name
            student.last_name = last_name
            student.form = form
            student.email = email
            student.phone = phone
            student.save()  # Save the updated student

            messages.success(request, f"Student '{first_name} {last_name}' updated successfully!")
            return redirect('lib-student-list')  # Redirect to a student list page (you can adjust this as needed)

        except Exception as e:
            messages.error(request, f"Error updating student: {str(e)}")  # Catch and display the error

    # For GET request, show the form pre-filled with the student's existing data
    context = {
        'title': f'Update Student - {student.first_name} {student.last_name}',
        'student': student,  # Pass the existing student object to pre-fill the form
        'student_form_choices': Student.STUDENT_FORM_CHOICES,  # Pass form choices here if needed
    }
    return render(request, 'Librarian/students-update.html', context)


@login_required(login_url='lib-login')
def SingleStudent(request, student_id):
    # Fetch the student object based on the student_id
    student = get_object_or_404(Student, student_id=student_id)

    # Fetch the borrow records for this student
    borrowed_books = Borrow.objects.filter(student=student).order_by('-borrow_date')

    # Get the associated fines for each borrowed book
    fines_history = Fine.objects.filter(borrow__student=student).order_by('-created_at')

    context = {
        'title': f'Student Profile - {student.first_name} {student.last_name}',
        'student': student,  # Student information
        'borrowed_books': borrowed_books,  # Borrowed books by the student
        'fines_history': fines_history,  # Fines allocated to the student
    }

    return render(request, 'Librarian/students-view.html', context)

@login_required(login_url='lib-login')
def DeleteStudent(request, student_id):
    # Fetch the student object based on the student_id
    student = get_object_or_404(Student, student_id=student_id)

    if request.method == 'POST':
        try:
            # First, delete all fines related to the student's borrowings
            Borrow.objects.filter(student=student).delete()  # Delete all borrow records
            Fine.objects.filter(borrow__student=student).delete()  # Delete all fines related to the student's borrowings

            # Now, delete the student
            student.delete()  # Delete the student record

            messages.success(request, f"Student '{student.first_name} {student.last_name}' has been deleted successfully.")
            return redirect('lib-student-list')  # Redirect to the student list page

        except Exception as e:
            messages.error(request, f"Error deleting student: {str(e)}")
            return redirect('lib-student-list')

    # For GET request, show the confirmation page to delete the student
    context = {
        'title': 'Delete Student',
        'student': student,  # Passing the student info to confirm the deletion
    }
    return render(request, 'Librarian/students-delete.html', context)

# ----------------------------------------------------------------------------------------------------------------------------------------------
#                                                       END STUDENT VIEWS
# ----------------------------------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------------------------------
#                                                       SUBJECTS VIEWS
# ----------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='lib-login')
def Subjects(request):
    # Get search and filter parameters from the request
    q = request.GET.get('q', '')  # Search by name
    
    # Base query for shelves
    subjects = Subject.objects.filter(
        Q(name__icontains=q)
    ).annotate(book_count=Count('book'))
     # Set up pagination with 10 items per page
    paginator = Paginator(subjects, 10)  # Show 10 shelves per page
    page_number = request.GET.get('page')  # Get the page number from the URL query parameters
    page_obj = paginator.get_page(page_number)  # Get the page object

    context = {
        'title': 'Subjects',
        'subjects': page_obj,  # Pass the paginated shelves to the template
        'current_q': q,  # Preserve the search query in the template
    }    
    return render(request, "Librarian/subjects.html", context)

@login_required(login_url='lib-login')
def NewSubject(request):

    if request.method == "POST":
        name = request.POST.get("subject_name")

        # Validate inputs
        if not name:
            messages.error(request, "Enter subject name!")
        else:
            Subject.objects.create(name=name)
            messages.success(request, f"{name} has been saved!")
    
    context = {
        'title': 'New Subject'
    }
    return render(request, 'Librarian/new-subject.html', context)


@login_required(login_url='lib-login')
def EditSubject(request, subject_id):
    # Get the shelf object by ID or raise a 404 if not found
    subject = get_object_or_404(Subject, id=subject_id)
    
    if request.method == "POST":
        name = request.POST.get("subject_name")
        
        
        # Validate inputs
        if not name:
            messages.error(request, "All fields are required!")
        else:
            # Update the shelf details
            subject.name = name
            subject.save()
            messages.success(request, f"{subject.name} updated successfully!")
            return redirect('shelves')  # Replace 'shelves' with your shelf list URL pattern
    
    context = {
        'title': 'Edit Subject',
        'subject': subject
    }
    return render(request, 'Librarian/edit-subject.html', context)


@login_required(login_url='lib-login')
def DeleteSubject(request, subject_id):
    # Get the shelf object by ID or raise a 404 if not found
    subject = get_object_or_404(Subject, id=subject_id)

    # Check if the request method is POST to confirm the deletion
    if request.method == "POST":
        subject.delete()
        messages.success(request, f"{subject.name} deleted successfully!")
        return redirect('shelves')  # Redirect to the shelves list page

    context = {
        'title': 'Delete Subject',
        'subject': subject
    }
    return render(request, 'Librarian/confirm-delete-subject.html', context)


# ----------------------------------------------------------------------------------------------------------------------------------------------
#                                                       END SUBJECTS VIEWS
# ----------------------------------------------------------------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------------------------------------------------------------
#                                                       FINES VIEWS
# ----------------------------------------------------------------------------------------------------------------------------------------------

@login_required(login_url='lib-login')
def FineList(request):
    q = request.GET.get('q', '').strip()  # Search by student ID or name
    status_filter = request.GET.get('status', 'all')  # Filter by fine status

    # Base queryset
    fines = Fine.objects.select_related('borrow__student', 'borrow__book')

    # Apply search filter
    if q:
        fines = fines.filter(
            Q(borrow__student__student_id__icontains=q) |
            Q(borrow__student__full_name__icontains=q)
        )

    # Apply status filter
    if status_filter == 'paid':
        fines = fines.filter(status='paid')
    elif status_filter == 'unpaid':
        fines = fines.filter(status='unpaid')

    # Pagination
    paginator = Paginator(fines.order_by('-id'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'title': 'Fines List',
        'fines': page_obj,
        'current_q': q,
        'current_status_filter': status_filter,
    }
    return render(request, 'Librarian/fines-list.html', context)

@login_required(login_url='lib-login')
def fine_detail(request, fine_id):
    fine = get_object_or_404(Fine, id=fine_id)
    return render(request, 'Librarian/fines-detail.html', {'fine': fine})

@login_required(login_url='lib-login')
def PayFine(request, fine_id):
    fine = get_object_or_404(Fine, id=fine_id)
    
    if fine.status == 'paid':
        messages.info(request, 'This fine is already paid.')
    else:
        fine.status = 'paid'
        fine.save()
        messages.success(request, 'Fine has been marked as paid.')

    return redirect('lib-books-borrowed')  # Or wherever appropriate

# ----------------------------------------------------------------------------------------------------------------------------------------------
#                                                       END FINES VIEWS
# ----------------------------------------------------------------------------------------------------------------------------------------------