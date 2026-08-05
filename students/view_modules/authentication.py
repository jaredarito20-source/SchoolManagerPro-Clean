from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

def login_view(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:

            login(
                request,
                user,
            )

            messages.success(
                request,
                f"Welcome {user.username}.",
            )

            return redirect("home")

        messages.error(
            request,
            "Invalid username or password.",
        )

    return render(
        request,
        "students/login.html",
    )

@login_required
def logout_view(request):

    logout(request)

    messages.success(
        request,
        "You have logged out successfully.",
    )

    return redirect("login")

@login_required
def change_password(request):

    if request.method == "POST":

        old_password = request.POST["old_password"]
        new_password = request.POST["new_password"]
        confirm_password = request.POST["confirm_password"]

        if not request.user.check_password(old_password):

            messages.error(
                request,
                "Current password is incorrect.",
            )

            return redirect("change_password")

        if new_password != confirm_password:

            messages.error(
                request,
                "Passwords do not match.",
            )

            return redirect("change_password")

        request.user.set_password(new_password)
        request.user.save()

        update_session_auth_hash(
            request,
            request.user,
        )

        messages.success(
            request,
            "Password changed successfully.",
        )

        return redirect("home")

    return render(
        request,
        "students/change_password.html",
    )

@login_required
def profile(request):

    return render(
        request,
        "students/profile.html",
        {
            "user": request.user,
        },
    )