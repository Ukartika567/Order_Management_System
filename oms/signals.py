from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import OrderItem,Order

@receiver(post_save, sender=OrderItem)
@receiver(post_delete, sender=OrderItem)
def update_total_price(sender, instance, **kwargs):
	order = instance.order
	order.total_price = sum(item.product.price * item.quantity for item in order.order.all())
	order.save()

##manage stock by signal
@receiver(post_save, sender=OrderItem)
def manage_stock(sender, instance, created, **kwargs):
    """Deduct stock on order & restore on cancel"""
    product = instance.product
    if instance.order.status == "Cancelled":
        product.stock_quantity += instance.quantity  # Restore stock
    else:
        product.stock_quantity -= instance.quantity  # Deduct stock
    product.save()

##send order notification
@receiver(post_save, sender=Order)
def send_order_notification(sender, instance, created, **kwargs):
    """Send email when order placed or canceled"""
    subject = "Order Update"
    message = f"Your order for {instance.orderedprod()} has been {'placed' if created else 'canceled'}."
    instance.user.email_user(subject, message)
