from django.db import models
from django.contrib.auth.models import AbstractUser 

# Create your models here.
class CustomUser(AbstractUser):
	email = models.EmailField(unique=True)
	first_name = models.CharField(max_length=30)
	last_name = models.CharField(max_length=30)
	is_seller = models.BooleanField(default=False)
	is_staff = models.BooleanField(default=False)
	
	groups = models.ManyToManyField(
        "auth.Group",
        related_name="customuser_set",
        blank=True
    )
	
	user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="customuser_permissions",
        blank=True
    )

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ['username','first_name','last_name']

	def __str__(self):
		return self.first_name

	class Meta:
		verbose_name = "OMS_User"
		# db_table = "OMS_User"

class Product(models.Model):
	name = models.CharField(max_length=100)
	price = models.DecimalField(max_digits=10, decimal_places=2)
	stock_quantity = models.PositiveIntegerField()
	seller = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.name

class Order(models.Model):
	STATUS_CHOICES=[
		('Placed', 'Placed'),
		('Confirmed', 'Confirmed'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
	]

	user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
	products = models.ManyToManyField(Product, through="OrderItem")
	total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Placed')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Order {self.id} - {self.user.first_name}"

	def save(self, *args, **kwargs):
		super().save(*args, **kwargs)  # Ensure order gets a primary key first
		total = sum(item.product.price * item.quantity for item in self.order.all())
		self.total_price = total
		super().save(*args, **kwargs)

	def orderedprod(self):
		return ",".join(set(str(item) for item in self.products.all()))		

class OrderItem(models.Model):
	order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order')
	product = models.ForeignKey(Product, on_delete=models.CASCADE)
	quantity = models.PositiveIntegerField()

	def __str__(self):
		return f"{self.quantity} x {self.product.name}"