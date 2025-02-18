from django.shortcuts import render, HttpResponse
from rest_framework import viewsets, status
from rest_framework.generics import CreateAPIView, GenericAPIView,UpdateAPIView
from .models import CustomUser, Product, Order, OrderItem
from .serializers import CustomUserSerializer, ProductSerializer, OrderItemSerializer, OrderSerializer,LoginSerializer
from rest_framework.permissions import AllowAny,IsAuthenticated, IsAdminUser
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import  method_decorator
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from django.contrib.auth import authenticate
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenBlacklistView
from .permissions  import IsSellerOrAdmin
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from .serializers import OrderSerializer, OrderCreateSerializer
from rest_framework.throttling import ScopedRateThrottle
import logging

# Configure logger
logger = logging.getLogger("api_logger")

# Create your views here.
def home(request):
    products = Product.objects.all()
    return render(request, 'home.html', {'products':products})

###User Registration
@method_decorator(csrf_exempt, name='dispatch')
class UserRegistrationAPIView(CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [AllowAny]

##User Login
class LoginAPIView(GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = authenticate(username=email, password=password)
        if not user:
            return Response({"error": "Invalid username or password"}, status=status.HTTP_400_BAD_REQUEST)

        #login the user
        # login(request, user) s

        # Generate JWT tokens
        refresh  = RefreshToken.for_user(user)
        access_token = refresh.access_token

        return Response({
            "message": "Login successful",
            "access_token": str(access_token),
            "refresh_token":str(refresh),
            "user": {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "user_type": "staff" if user.is_staff else "seller" if user.is_seller else "customer"
            }
        }, status=status.HTTP_200_OK)


##User logout
# class LogoutAPIView(GenericAPIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         refresh_token = request.data.get("refresh_token")
        
#         if not refresh_token:
#             return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             # Ensure it is a refresh token
#             token = RefreshToken(refresh_token)
#             print('token-', token, token.token_type)
#             if token.token_type != "refresh":
#                 return Response({"error": "Token is not a refresh token"}, status=status.HTTP_400_BAD_REQUEST)

#             token.blacklist()
#             return Response({"message": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)
        
#         except Exception as e:
#             return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)

class LogoutAPIView(TokenBlacklistView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        # if response.status_code == 200 or response.status_code == 205:
        #     logout(request)  # Clear session 
        print('response.status_code---', response.status_code)
        if response.status_code in [200, 205]:
            access_token = request.data.get('access_token')
            
            # Blacklist access token
            print('access_token-',access_token)
            if access_token:
                try:
                    print('bb-')
                    access = AccessToken(access_token)
                    access.blacklist()
                except Exception as e:
                    return Response({"error": "Invalid access token"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Logout successful"}, status=status.HTTP_205_RESET_CONTENT)


##############*********Product API**************#############
class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]

    # print('q-', queryset.query)
    logger.info('q- %s',queryset.query )
    
    filterset_fields = {
        'price': ['gte', 'lte'],
        'stock_quantity': ['gte'],
    }
    
    ordering_fields = ['price', 'created_at']  

    def get_permissions(self):
        print(f"Request User: {self.request.user}")
        print(f"User is authenticated: {self.request.user.is_authenticated}")
        print(f"User is staff: {self.request.user.is_staff}")

        if self.action in ['list', 'retrieve']:  
            return [AllowAny()]  # Anyone can view products
        return [IsSellerOrAdmin()]  # Only sellers & admin can modify products


    def perform_create(self, serializer):
        """Assign seller_id from the logged-in user"""
        user = self.request.user
        if not user.is_authenticated:
            raise PermissionDenied("Authentication is required to add a product.")

        if not (user.is_staff or user.is_seller):  # Ensure user is a seller or admin
            raise PermissionDenied("Only sellers or admins can add products.")

        serializer.save(seller=user)  # Automatically set seller


############**********Order API***********#########

class OrderCreateView(CreateAPIView):
    """API to place an order"""
    queryset = Order.objects.all()
    serializer_class = OrderCreateSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes= [ScopedRateThrottle]
    throttle_scope = 'order'

    def perform_create(self, serializer):
        """Validate stock & create order"""
        user = self.request.user
        order = serializer.save(user=user)  
        return Response({"message": "Order placed successfully!", "order_id": order.id}, status=status.HTTP_201_CREATED)

class OrderCancelView(UpdateAPIView):
    """API to cancel an order"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        order = self.get_object()
        if order.status == "Cancelled":
            return Response({"error": "Order already canceled!"}, status=status.HTTP_400_BAD_REQUEST)

        order.status = "Cancelled"
        order.save()
        return Response({"message": "Order canceled successfully!"}, status=status.HTTP_200_OK)


#######******Admin API*************########
class BulkUpdateOrderStatusView(UpdateAPIView):
    """API to update multiple orders' statuses in bulk (Admin Only)"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]

    def update(self, request, *args, **kwargs):
        order_ids = request.data.get("order_ids", [])  # List of order IDs
        new_status = request.data.get("status", None)  # New status to set

        if not order_ids or not new_status:
            return Response({"error": "Provide order_ids and new status"}, status=400)

        # Update orders in bulk
        orders = Order.objects.filter(id__in=order_ids)
        orders.update(status=new_status)

        return Response({"message": f"Updated {len(orders)} orders to '{new_status}'"}, status=200)

##for notifucation
import threading
from django.core.mail import send_mail
def send_order_email(user_email, order_id, status):
    """Function to send email asynchronously"""
    subject = f"Order {order_id} - {status}"
    message = f"Your order (ID: {order_id}) is now {status}."
    send_mail(subject, message, "admin@yourshop.com", [user_email])

class OrderCreateView(CreateAPIView):
    """API to place an order"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        order = serializer.save(user=self.request.user)  # Save order for user
        # Send order confirmation in a separate thread
        email_thread = threading.Thread(target=send_order_email, args=(self.request.user.email, order.id, order.status))
        email_thread.start()



###for bulk order
from concurrent.futures import ThreadPoolExecutor
from django.db.models import Count

class BulkProcessLargeOrdersView(GenericAPIView):
    """Admin API to process large orders asynchronously"""
    permission_classes = [IsAdminUser]

    def post(self, request, *args, **kwargs):
        large_orders = Order.objects.annotate(total_items=Count("order")).filter(total_items__gt=50)
        
        if not large_orders.exists():
            return Response({"message": "No large orders to process"}, status=200)

        # Use multithreading to process orders
        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(self.process_large_order, large_orders)

        return Response({"message": f"Processing {large_orders.count()} large orders"}, status=200)

    def process_large_order(self, order):
        """Processing logic for large orders"""
        print(f"Processing large order {order.id} with {order.order.all().count()} items.")


##########**********Customer API***********########
from rest_framework import generics, permissions
from .models import CustomUser
from .serializers import CustomerSerializer

class CustomerListCreateView(generics.ListCreateAPIView):
    """API to list all customers and add new customers."""
    queryset = CustomUser.objects.filter(is_seller=False)
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]  

class CustomerDetailView(generics.RetrieveUpdateDestroyAPIView):
    """API to retrieve, update, or delete a customer."""
    queryset = CustomUser.objects.filter(is_seller=False)
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated]  


#########********Generate Inventry ***********##########
import openpyxl
from django.http import HttpResponse
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Order

class OrderReportDownloadView(generics.GenericAPIView):
    """API to generate and return an Excel report"""
    permission_classes = [IsAdminUser]  # Restrict access

    def get(self, request, *args, **kwargs):
        """Generates an Excel report of orders and returns as a downloadable file"""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Order Report"

        # Define Excel Headers
        headers = ["Order ID", "User", "Products", "Status", "Total Price"]
        ws.append(headers)

        # Fetch only orders related to the logged-in user
        orders = Order.objects.filter(user=request.user).prefetch_related("order__product")

        if not orders.exists():
            return Response({"message": "No orders found."}, status=status.HTTP_404_NOT_FOUND)

        for order in orders:
            products = ", ".join([f"{item.product.name} (x{item.quantity})" for item in order.order.all()])
            ws.append([order.id, order.user.email, products, order.status, order.total_price])

        # Prepare the HTTP response with Excel file
        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="order_report.xlsx"'
        wb.save(response)

        return response
