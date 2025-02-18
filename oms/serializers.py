from rest_framework import serializers
from .models import CustomUser, Product, Order, OrderItem

class CustomUserSerializer(serializers.ModelSerializer):
    USER_TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('seller', 'Seller'),
        ('staff', 'Staff'),
    ]
    user_type = serializers.ChoiceField(choices=USER_TYPE_CHOICES, write_only=True, required=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    user_type_display = serializers.SerializerMethodField() ##custom field return after registration

    class Meta:
        model = CustomUser
        fields = [ 'first_name', 'last_name','username', 'email', 'password', 'user_type','user_type_display']

    def get_user_type_display(self, obj):
        """Determine user type based on is_seller and is_staff."""
        if obj.is_staff:
            return "staff"
        elif obj.is_seller:
            return "seller"
        return "customer" 

    def create(self, validated_data):
        """Create and return a new user with hashed password"""
        user_type = validated_data.pop('user_type')
        password = validated_data.pop('password')

        user = CustomUser(**validated_data)
        user.set_password(password)
        # Assign user type
        if user_type == 'customer':
            user.is_seller = False
            user.is_staff = False
        elif user_type == 'seller':
            user.is_seller = True
            user.is_staff = False
        elif user_type == 'staff':
            user.is_seller = False
            user.is_staff = True

        user.save()
        return user
    

##login serializer
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

class ProductSerializer(serializers.ModelSerializer):
    seller = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = Product
        fields = ['name', 'price', 'stock_quantity', 'seller']

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['order', 'product', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    order_items = OrderItemSerializer(source='order', many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = ['user', 'order_items', 'total_price', 'status', 'created_at', 'updated_at']

from rest_framework import serializers
from .models import Order, OrderItem

##order creation serializers
class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an order"""
    order_items = OrderItemSerializer(many=True, write_only=True)

    class Meta:
        model = Order
        fields = ['order_items']

    def create(self, validated_data):
        """Create order & manage stock"""
        order_items_data = validated_data.pop('order_items')
        order = Order.objects.create(**validated_data)

        for item in order_items_data:
            OrderItem.objects.create(order=order, **item)

        return order

##for customer API
class CustomerSerializer(serializers.ModelSerializer):
    order_count = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'email', 'is_seller', 'order_count']

    def get_order_count(self, obj):
        """Return the number of orders placed by the customer."""
        return Order.objects.filter(user=obj).count()
