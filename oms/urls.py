from django.urls import path, include
from django.contrib.auth import views as auth_views
from .import views
from rest_framework.routers import DefaultRouter
from .views import OrderCreateView, OrderCancelView
from .views import OrderReportDownloadView
from .views import CustomerListCreateView, CustomerDetailView

router = DefaultRouter()
router.register('products', views.ProductViewSet, basename='products')

urlpatterns = [
	path('home/', views.home, name='home'),
	path('', include(router.urls)),
	# path('auth/', include('rest_framework.urls',namespace='rest_framework')),
	path('register/', views.UserRegistrationAPIView.as_view(), name='register'),
	path('login/', views.LoginAPIView.as_view(), name='login'),
    path('logout/', views.LogoutAPIView.as_view(), name='logout'),

	##Order api
	path('orders/', OrderCreateView.as_view(), name='create_order'),
    path('orders/<int:pk>/cancel/', OrderCancelView.as_view(), name='cancel_order'),

	###generate inventry
	path("download-order-report/", OrderReportDownloadView.as_view(), name="download-order-report"),

	###customer API
	path('customers/', CustomerListCreateView.as_view(), name='customer-list-create'),
    path('customers/<int:pk>/', CustomerDetailView.as_view(), name='customer-detail'),

]