from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum
from django.http import HttpResponse

from reportlab.pdfgen import canvas

from students.models import *

from students.decorators import (
    admin_or_bursar,
    in_group,
)

from students.utils import (
    draw_school_header,
    draw_school_footer,
)

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Store Keeper",
)
def inventory_list(request):

    items = InventoryItem.objects.select_related(
        "category"
    ).all().order_by(
        "name"
    )

    return render(
        request,
        "inventory/inventory_list.html",
        {
            "items": items,
        },
    )

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Store Keeper",
)
def add_inventory_item(request):

    categories = InventoryCategory.objects.all()

    if request.method == "POST":

        InventoryItem.objects.create(

            category=InventoryCategory.objects.get(
                id=request.POST["category"]
            ),

            name=request.POST["name"],

            quantity=request.POST["quantity"],

            unit=request.POST["unit"],

            minimum_stock=request.POST["minimum_stock"],

            location=request.POST["location"],

            description=request.POST["description"],

        )

        messages.success(
            request,
            "Inventory item added successfully."
        )

        return redirect("students:inventory_list")

    return render(
        request,
        "inventory/add_inventory_item.html",
        {
            "categories": categories,
        },
    )


@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Store Keeper",
)
def edit_inventory_item(request, id):

    item = get_object_or_404(
        InventoryItem,
        id=id,
    )

    categories = InventoryCategory.objects.all()

    if request.method == "POST":

        item.category = InventoryCategory.objects.get(
            id=request.POST["category"]
        )

        item.name = request.POST["name"]
        item.quantity = request.POST["quantity"]
        item.unit = request.POST["unit"]
        item.minimum_stock = request.POST["minimum_stock"]
        item.location = request.POST["location"]
        item.description = request.POST["description"]

        item.save()

        messages.success(
            request,
            "Inventory item updated successfully."
        )

        return redirect("students:inventory_list")

    return render(
        request,
        "inventory/edit_inventory_item.html",
        {
            "item": item,
            "categories": categories,
        },
    )

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Store Keeper",
)
def delete_inventory_item(request, id):

    item = get_object_or_404(
        InventoryItem,
        id=id,
    )

    if request.method == "POST":

        item.delete()

        messages.success(
            request,
            "Inventory item deleted successfully."
        )

        return redirect("students:inventory_list")

    return render(
        request,
        "inventory/delete_inventory_item.html",
        {
            "item": item,
        },
    )

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Store Keeper",
)
def inventory_category_list(request):

    categories = InventoryCategory.objects.all().order_by("name")

    return render(
        request,
        "inventory/inventory_category_list.html",
        {
            "categories": categories,
        },
    )

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Store Keeper",
)
def add_inventory_category(request):

    if request.method == "POST":

        InventoryCategory.objects.create(
            name=request.POST["name"]
        )

        messages.success(
            request,
            "Inventory category added successfully."
        )

        return redirect("students:inventory_category_list")

    return render(
        request,
        "inventory/add_inventory_category.html",
    )

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Store Keeper",
)
def receive_stock(request, id):

    item = get_object_or_404(
        InventoryItem,
        id=id,
    )

    if request.method == "POST":

        quantity = int(
            request.POST["quantity"]
        )

        item.quantity += quantity

        item.save()

        StockTransaction.objects.create(

            item=item,

            transaction_type="RECEIVED",

            quantity=quantity,

            remarks=request.POST["remarks"],

            recorded_by=request.user,

        )

        messages.success(
            request,
            "Stock received successfully."
        )

        return redirect("students:inventory_list")

    return render(
        request,
        "inventory/receive_stock.html",
        {
            "item": item,
        },
    )

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Store Keeper",
)
def issue_stock(request, id):

    item = get_object_or_404(
        InventoryItem,
        id=id,
    )

    if request.method == "POST":

        quantity = int(request.POST["quantity"])

        if quantity > item.quantity:

            messages.error(
                request,
                "Not enough stock available."
            )

            return render(
                request,
                "inventory/issue_stock.html",
                {
                    "item": item,
                },
            )
            

        item.quantity -= quantity
        item.save()

        StockTransaction.objects.create(

            item=item,

            transaction_type="ISSUED",

            quantity=quantity,

            remarks=request.POST["remarks"],

            recorded_by=request.user,

        )

        messages.success(
            request,
            "Stock issued successfully."
        )

        return redirect("students:inventory_list")

    return render(
        request,
        "inventory/issue_stock.html",
        {
            "item": item,
        },
    )

@login_required
@in_group(
    "Administrators",
    "Head Teacher",
    "Store Keeper",
)
def stock_transaction_list(request):

    transactions = StockTransaction.objects.select_related(
        "item",
        "recorded_by",
    ).order_by("-transaction_date", "-id")

    return render(
        request,
        "inventory/stock_transaction_list.html",
        {
            "transactions": transactions,
        },
    )