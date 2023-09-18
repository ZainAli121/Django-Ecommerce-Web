from django.shortcuts import render, redirect
from .models import *
from django.http import JsonResponse
import json
import datetime
from .utils import cookieCart, cartData, guestOrder
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User

# Create your views here.
def store(request):
    data = cartData(request)
    cartItems = data['cartItems']

    products = Product.objects.all()
    context = {'products': products, 'cartItems': cartItems}
    return render(request, 'store/store.html', context)

def searchMatch(query, item):
    '''return true only if query matches the item'''
    if query in item.name.lower():
        return True
    else:
      return False

def search(request):
    query = request.GET.get('search')
    data = cartData(request)
    cartItems = data['cartItems']

    products = Product.objects.filter(name__icontains=query)
    prod = [item for item in products if searchMatch(query, item)]
    if len(products) != 0:
        context = {'products': products, 'cartItems': cartItems, 'msg': ""}
        print("The length of products is: ", len(products))

    if len(products) == 0 or len(query)<2:
        context = {'msg' : "No valid search result found. Please make sure to enter relevant search query"}
        print("The length of products is: ", len(products))
    return render(request, 'store/search.html', context)


def cart(request):
    data = cartData(request)
    items = data['items']
    order = data['order']
    cartItems = data['cartItems']
            
    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/cart.html', context)

def checkout(request):
    data = cartData(request)
    items = data['items']
    order = data['order']
    cartItems = data['cartItems']
        
    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/checkout.html', context)

def updateItem(request):
    
        data = json.loads(request.body)
        productId = data['productId']
        action = data['action']
    
        print('Action:', action)
        print('ProductID:', productId)
    
        customer = request.user.customer
        product = Product.objects.get(id=productId)
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
    
        orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)
    
        if action == 'add':
            orderItem.quantity = (orderItem.quantity + 1)
        elif action == 'remove':
            orderItem.quantity = (orderItem.quantity - 1)
    
        orderItem.save()
    
        if orderItem.quantity <= 0:
            orderItem.delete()
    
        return JsonResponse('Item was added', safe=False)

def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)

    else:
        customer, order = guestOrder(request, data)

    total = float(data['form']['total'])
    order.transaction_id = transaction_id

    if total == order.get_cart_total:
        order.complete = True
    order.save()

    if order.shipping == True:
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=data['shipping']['address'],
            city=data['shipping']['city'],
            state=data['shipping']['state'],
            zipcode=data['shipping']['zipcode'],
            )
    return JsonResponse('Payment submitted..', safe=False)

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username = username).exists():
            messages.success(request, 'Username already exists')

        user = User.objects.create_user(username=username, password=password, email=email)
        customer = Customer.objects.create(user=user, name=username, email=email)
        user.save()
        customer.save()
        messages.success(request, 'Account was created for ' + username)
    return render(request, 'store/register.html')



def loginuser(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
    
        user = authenticate(request, username=username, password=password)
    
        if user is not None:
            login(request, user)
            try:
                customer = user.customer
            except Customer.DoesNotExist:
                customer = None
            if customer:
                return redirect('/')

        else:
            messages.success(request, 'Username OR password is incorrect')
            return redirect('login')
    return render(request, 'store/login.html')