from django.contrib.auth import logout
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.shortcuts import redirect
from django.urls import reverse_lazy

from .forms import LoginForm


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = "auth/login.html"

    def form_valid(self, form):
        remember_me = form.cleaned_data.get("remember_me")
        response = super().form_valid(form)
        if remember_me:
            self.request.session.set_expiry(1209600)  # 2 weeks
        else:
            self.request.session.set_expiry(0)  # expire on browser close
        return response


def logout_view(request):
    logout(request)
    return redirect("login")


class ForcePasswordChangeView(PasswordChangeView):
    template_name = "auth/password_change.html"
    success_url = reverse_lazy("password_change_done")

    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.request.user
        if user.must_change_password:
            user.must_change_password = False
            user.save(update_fields=["must_change_password"])
        return response
