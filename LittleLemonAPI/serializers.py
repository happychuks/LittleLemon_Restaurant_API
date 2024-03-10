from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Category,MenuItem, Cart, Order, OrderItem
from datetime import datetime


class CategorySerializer (serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'slug']


class UserSerializer(serializers.ModelSerializer):
 class Meta:
  model = User
  fields = ['id', 'username','email']
  
class CategorySerializer(serializers.ModelSerializer):
  class Meta:
    model = Category
    fields = ['title']
  
class MenuItemSerializer(serializers.ModelSerializer):
  category = CategorySerializer(read_only=True)
  category_id = serializers.IntegerField(write_only = True)
  class Meta:
    model = MenuItem
    fields = ['id','title', 'price', 'featured', 'category', 'category_id']
    
    
class CartSerializer(serializers.ModelSerializer):
  user = serializers.StringRelatedField()
  menuitem = serializers.StringRelatedField()
  class Meta:
    model = Cart
    fields = ['id','user','menuitem','quantity', 'unit_price', 'price']
    
class OrderItemSerializer(serializers.ModelSerializer):
    menuitem = serializers.CharField(source = 'menuitem.title',read_only=True)
    unit_price = serializers.DecimalField(max_digits=6, decimal_places=2, source='menuitem.price', read_only=True)
    price = serializers.DecimalField(max_digits=6, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['menuitem', 'quantity', 'unit_price', 'price']
    
    

class OrderSerializer(serializers.ModelSerializer):
    orderitem_set = OrderItemSerializer(many=True)
    date = serializers.SerializerMethodField()
    user = serializers.StringRelatedField()

    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew', 'status', 'total', 'date', 'orderitem_set']
        
    def get_date(self, obj):
        dt = datetime.combine(obj.date, datetime.min.time())
        return dt.isoformat()
    





 