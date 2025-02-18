from django.contrib import admin

# Register your models here.
from .models import CustomUser, Product, Order,OrderItem  # Import your models

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_seller', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_seller', 'is_staff')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'price', 'stock_quantity', 'seller', 'created_at', 'updated_at')
    search_fields = ('name', 'seller__email')
    list_filter = ('price', 'stock_quantity')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id','user', 'orderedprod','total_price', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email',)

@admin.register(OrderItem)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity')
    list_filter = ('order', 'quantity')
    search_fields = ('order__status',)
