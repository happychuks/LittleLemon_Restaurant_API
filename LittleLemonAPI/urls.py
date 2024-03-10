from django.urls import  path
from . import views

urlpatterns = [
 path('categories', views.CategoriesView.as_view()),
 path('groups/manager/users', views.managers),
 path('groups/manager/users/<int:pk>', views.manager_delete),
 path('groups/delivery/users', views.delivery_group),
 path('groups/delivery/users/<int:pk>', views.remove_from_delivery_group),
 path('menu-item/<int:pk>', views.single_menu_item),
 path('menu-item', views.menu_items),
 path('cart/menu-items', views.cart_view),
 path('orders/', views.order_view),
 path('orders/<int:pk>', views.single_order_view),
]