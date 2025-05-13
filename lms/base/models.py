from django.db import models
from datetime import timedelta, date
from decimal import Decimal
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.contrib.auth.models import User


class Subject(models.Model):
    SUBJECT_LEVEL_CHOICES = [
        ('ordinary level','Ordinary level'),
        ('advanced level','Advanced level')
    ]
    name = models.CharField(max_length=200, unique=True)
    level = models.CharField(max_length=18, choices=SUBJECT_LEVEL_CHOICES)

    def __str__(self):
        return f"{self.level}: {self.name}"
    
class Shelf(models.Model):
    SHELF_LEVEL_CHOICES = [
        ('ordinary level','Ordinary level'),
        ('advanced level','Advanced level')
    ]
    name = models.CharField(max_length=200, unique=True)
    capacity = models.IntegerField()
    level = models.CharField(max_length=18, choices=SHELF_LEVEL_CHOICES)

   

    def __str__(self):
        return self.name

    def is_full(self):
        return self.book_set.count() >= self.capacity

    def current_load(self):
        return self.book_set.count()


class Book(models.Model):
    BOOK_FORM_CHOICES = [
        ('1','1'),
        ('2','2'),
        ('3','3'),
        ('4','4'),
        ('5','5'),
        ('6','6'),
    ]
    isbn = models.CharField(max_length=13, unique=True)
    author = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    publication_date = models.DateField()
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    shelf = models.ForeignKey(Shelf, on_delete=models.CASCADE)
    form = models.CharField(max_length=1, choices=BOOK_FORM_CHOICES)  # Corrected this line
    price = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)  # Add price field

    created_at = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.shelf.book_set.count() >= self.shelf.capacity:
            raise ValueError(f"The shelf '{self.shelf.name}' is full. Please choose another shelf.")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Student(models.Model):
    STUDENT_FORM_CHOICES = [
        ('1E','1E'),
        ('1W','1W'),
        ('1N','1N'),
        ('1S','1S'),
        ('2E','2E'),
        ('2W','2W'),
        ('2N','2N'),
        ('2S','2S'),
        ('3E','3E'),
        ('3W','3W'),
        ('3N','3N'),
        ('3S','3S'),
        ('4E','4E'),
        ('4W','4W'),
        ('4N','4N'),
        ('4S','4S'),
        ('5S','5S'),
        ('5C','5C'),
        ('5A','5A'),
        ('6S','6S'),
        ('6C','6C'),
        ('6A','6A'),
    ]

    STUDENT_GENDER_CHOICES = [
        ('female', 'Female'),
        ('male', 'Male')
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    student_id = models.CharField(max_length=20, unique=True)
    gender = models.CharField(max_length=7, choices=STUDENT_GENDER_CHOICES, default='Male')
    form = models.CharField(max_length=2, choices=STUDENT_FORM_CHOICES)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    created_at = models.DateField(auto_now_add=True)

    def total_fines(self):
        """
        Calculates the total fines from all borrow records, regardless of the return status.
        """
        total = sum(borrow.fine for borrow in self.borrows.all())
        return round(total, 2)
    
   
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"





class Borrow(models.Model):
    STATUS_CHOICES = [
        ('borrowed', 'Borrowed'),
        ('returned', 'Returned'),
        ('lost', 'Lost'),
        ('damaged', 'Damaged'),
    ]

    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name="borrows")
    book = models.ForeignKey('Book', on_delete=models.CASCADE, related_name="borrows")
    borrow_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='borrowed')
    updated_at = models.DateField(auto_now=True)

    def calculate_fine(self):
        """Calculate fines based on the status of the borrow."""
        print(f"Calculating fine for borrow with status {self.status}")

        if self.status == 'returned' and self.return_date and self.due_date:
            # Fine for late return
            overdue_days = (self.return_date - self.due_date).days
            if overdue_days > 0:
                print(f"Overdue by {overdue_days} days")
                return Decimal(overdue_days) * Decimal('0.50'), f"Overdue by {overdue_days} days"
            return Decimal('0.00'), None  # No fine if returned on time
        
        elif self.status == 'lost':
            # Fine for lost book
            print("Book lost")
            return Decimal(self.book.price), "Book lost"
        
        elif self.status == 'damaged':
            # Fine for damaged book
            print("Book damaged")
            return Decimal(self.book.price) * Decimal('0.5'), "Book damaged (50% of book price)"

        print("No fine")
        return Decimal('0.00'), None  # No fine if no condition met

    @property
    def fine(self):
        fine_amount, _ = self.calculate_fine()  # Use the existing `calculate_fine` method
        return fine_amount

    def save(self, *args, **kwargs):
        # Set the due date if not already set
        if not self.due_date:
            self.due_date = self.borrow_date + timedelta(days=14)

        # Calculate the fine amount and reason
        fine_amount, reason = self.calculate_fine()

        # Only create or update a fine record if the fine amount is greater than zero
        if fine_amount > 0 and reason:
            fine, created = Fine.objects.update_or_create(
                borrow=self,
                defaults={'amount': fine_amount, 'reason': reason, 'status': 'unpaid'}
            )

            # If the fine record was created, it means it's a new fine
            if created:
                print(f"New fine created: {fine}")
            else:
                print(f"Fine updated: {fine}")

        # Save the changes to the Borrow record
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} borrowed {self.book}"

class Fine(models.Model):
    STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
    ]
    
    borrow = models.ForeignKey('Borrow', on_delete=models.CASCADE, related_name='fines')
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    reason = models.CharField(max_length=255, help_text="Reason for the fine (e.g., overdue, lost book, damaged book).")
    status = models.CharField(max_length=6, choices=STATUS_CHOICES, default='unpaid')
    created_at = models.DateField(auto_now_add=True)
    paid_at = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Fine for {self.borrow.book.title} - {self.amount} ({self.status})"
