from django.shortcuts import render,get_object_or_404
from django.contrib.auth.models import User,Group
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from  rest_framework import status
from .serializers import UserSerializer,MenuItemSerializer, CartSerializer, OrderSerializer, OrderItemSerializer, CategorySerializer
from rest_framework import generics
from  .models import MenuItem, Cart, Order, OrderItem, Category
import datetime
from django.core.paginator import Paginator, EmptyPage
from rest_framework.throttling import  AnonRateThrottle, UserRateThrottle

# Create your views here.


# ======================================================
# Category views
# ======================================================
class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        permission_classes = []
        if self.request.method != 'GET':
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]


#  =======================================================
# This block belongs to the menu-items
# ========================================================
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def menu_items(request):
 if request.method == 'GET':
  items = MenuItem.objects.select_related('category').all()
  category_name = request.query_params.get('category')
  price = request.query_params.get('price')
  search = request.query_params.get('search')
  perpage =request.query_params.get('perpage', default=2)
  page = request.query_params.get('page', default=1)
  if category_name:
      items = items.filter(category__title =category_name)
  if price:
      items = items.filter(price__lte =price)
  if search:
      items = items.filter(title__icontains =search)
  paginator = Paginator(items, per_page=perpage)
  try:
      items =paginator.page(number=page)
  except EmptyPage:
    items =[]

  serialized_item = MenuItemSerializer(items, many=True)
  return Response(serialized_item.data)
 
 elif  request.method == 'POST':
     if request.user.groups.filter(name='manager').exists():
         serializer= MenuItemSerializer(data=request.data)
         if serializer.is_valid():
             serializer.save()
             return Response(serializer.data, status.HTTP_201_CREATED)
         return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
     return Response({'message':'Access Denied'}, status.HTTP_401_UNAUTHORIZED)


@api_view(['GET', 'PUT', 'DELETE','PATCH'])
@permission_classes([IsAuthenticated])
@throttle_classes([UserRateThrottle])
def single_menu_item(request, pk):
    try:
        item = MenuItem.objects.get(pk=pk)
    except ObjectDoesNotExist:
        return Response({'message':'Item does not exist'},status.HTTP_404_NOT_FOUND)
    if request.method == 'GET':
        serializer = MenuItemSerializer(item)
        return Response(serializer.data)
    if request.method == 'PUT':
        if request.user.groups.filter(name='manager').exists():
            serializer = MenuItemSerializer(item,data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Access Denied'}, status.HTTP_401_UNAUTHORIZED)
    if request.method == 'PATCH':
        if request.user.groups.filter(name='manager').exists():
            serializer = MenuItemSerializer(item,data=request.data, partial= True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Access Denied'}, status.HTTP_401_UNAUTHORIZED)
    if request.method == 'DELETE':
            if request.user.groups.filter(name='manager').exists():
                item.delete()
                return Response({'message': 'Item has been deleted'})
            return Response({'message': 'Access Denied'}, status.HTTP_401_UNAUTHORIZED)
                
        
    
    
# ========================================
# This block allows Admin to add and remove
# to the manager group
# ========================================

@api_view(['GET','POST'])
@permission_classes([IsAdminUser])
@throttle_classes([UserRateThrottle])
def managers(request):
    if request.method == 'GET':
        users = User.objects.filter(groups__name='manager')
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    if request.method == 'POST':
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username=username)
            manager = Group.objects.get(name='manager',)
            manager.user_set.add(user)
            return Response({'message': 'Added sucessfully'}, status.HTTP_201_CREATED)
        return Response({'message': 'User does not exist'}, status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def manager_delete(request, pk):
    '''
    Allows the Admin to remove a user from the manager group using
    the provided primary key provided in the the request method
    
    '''
    
    user = get_object_or_404(User, id = pk)
    manager = Group.objects.get(name ='manager')
    manager.user_set.remove(user)
    return Response({'message': 'User removed '}, status.HTTP_200_OK)
    

# =============================================
#  This block alows manager to add and remove
# to the delivery group
# =============================================

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def delivery_group(request):
    '''
    Gets all users in the delivery crew group, and also adds user to group
    '''
    if request.user.groups.filter(name='manager').exists():
        if request.method == 'GET':
            users = User.objects.filter(groups__name ='Delivery crew')
            serializer = UserSerializer(users, many=True)
            return Response(serializer.data)
        if request.method == 'POST':
            username = request.data['username']
            user =get_object_or_404(User, username=username)
            delivery_crew = Group.objects.get(name = 'Delivery crew')
            delivery_crew.user_set.add(user)
            return Response({'message':'User has been added to delivery crew'},status.HTTP_201_CREATED)
    return Response({'message':'Not Authorized'}, status.HTTP_401_UNAUTHORIZED)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_delivery_group(request, pk):
    if request.user.groups.filter(name='manager').exists():
        user = get_object_or_404(User, id =pk)
        delivery_crew = Group.objects.get(name='Delivery crew')
        delivery_crew.user_set.remove(user)
        return Response({'message': 'User has been removed from group'}, status.HTTP_200_OK)
    
    
    
    # ==================================================
    # This block is the Cart View which allows customer 
    # to add, create and delete cart
    # ==================================================
    
        
@api_view(['GET','POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def cart_view(request):
    user = request.user
    if request.method == 'GET':
        cart = Cart.objects.filter(user=user)
        serializer = CartSerializer(cart, many=True)
        return Response(serializer.data, status.HTTP_200_OK)
    
    if request.method == 'POST':
        requested_menuitem = request.data['menuitem']
        quantity = request.data['quantity']
        menuitem = get_object_or_404(MenuItem, title = requested_menuitem)
        cart_exist = Cart.objects.filter(user=user, menuitem=menuitem).exists()
        if cart_exist:
            cart = Cart.objects.get(user=user, menuitem=menuitem)
            cart.quantity += int(quantity)
            cart.price = cart.quantity * cart.unit_price
            cart.save()
            return Response({'message': 'Menuitem Added'})
        price = menuitem.price * int(quantity)
        cart = Cart.objects.create(user=user,menuitem=menuitem,quantity=quantity,unit_price =menuitem.price,price=price)
        return Response({'message': 'Menuitem Created'})
    if request.method == 'DELETE':
        Cart.objects.filter(user=user).delete()
        return Response({'message':'Cart emptied'})
 
#==================================================== 
# This order view starts from here
# ===================================================


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])  
@throttle_classes([UserRateThrottle]) 
def order_view(request):
    user = request.user
    if request.method == 'GET':
        if request.user.groups.filter(name ='manager').exists() or request.user.groups.filter(name='Delivery crew').exists():
            order= Order.objects.prefetch_related('orderitem_set').all()
            rstatus = request.query_params.get('status')
            if rstatus:
                order = order.filter(status=rstatus)
                
            serializer= OrderSerializer(order, many=True)
            return Response(serializer.data, status.HTTP_200_OK)
        orders = Order.objects.filter(user=user).prefetch_related('orderitem_set')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    
    if request.method == 'POST':
        cart_items = Cart.objects.filter(user=user)
        if not cart_items:
            return Response({'message': 'No item in the cart'}, status.HTTP_400_BAD_REQUEST)
        today = datetime.date.today()
        today_str = today.strftime('%Y-%m-%d')
        order = Order.objects.create(user=user, total=0, date =today_str )
        order_items =[]
        for cart_item in cart_items:
            order_item = OrderItem(
                order=order,
                menuitem = cart_item.menuitem,
                quantity = cart_item.quantity,
                unit_price =cart_item.menuitem.price,
                price = cart_item.quantity * cart_item.menuitem.price
                
                
            )
            order_items.append(order_item)
        
        OrderItem.objects.bulk_create(order_items)
        total = sum([order_item.price for order_item in order_items])
        order.total = total
        order.save()

        cart_items.delete()
        
        serializer = OrderItemSerializer(order_items, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET','PATCH','DELETE'])
@permission_classes([IsAuthenticated])
def single_order_view(request, pk):
    user = request.user
    if request.method == 'GET':
        if request.user.groups.filter(name='manager').exists():
            order= get_object_or_404(Order, pk=pk)
            order_items = OrderItem.objects.filter(order=order)
            serializer = OrderItemSerializer(order_items, many=True)
            return Response(serializer.data, status.HTTP_200_OK)
        try:
            order = Order.objects.get(pk=pk, user= user)
            order_items = OrderItem.objects.filter(order=order)
            serializer = OrderItemSerializer(order_items, many=True)
            return Response(serializer.data, status.HTTP_200_OK)

        
        except ObjectDoesNotExist:
            return Response({'message': 'Order not found'},status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'PATCH':
        if request.user.groups.filter(name='manager').exists() or request.user.groups.filter(name='Delivery crew').exists():
            order_items = Order.objects.get(pk=pk)
            serialized_item = OrderSerializer(order_items,data=request.data, partial=True)
            serialized_item.is_valid(raise_exception=True)
            serialized_item.save()
            return Response(serialized_item.data, status.HTTP_200_OK)
        return Response({'message':'You are not authorized to pefrorm this operation '}, status.HTTP_401_UNAUTHORIZED)
    if request.method == 'DELETE':
        if request.user.groups.filter(name='manager').exists():
            order = get_object_or_404(Order,pk=pk)
            order.delete()
            return Response({'message':'Order deleted successfully'})
            

        
    
    
    
    
                
        
        
        
 
        
            
        
        
            
    
 
 
 
 