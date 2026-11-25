from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import AvailabilityForm, CostCalculatorForm, ToolForm
from .models import Category, Tool
from .services import calculate_rental_amounts, get_available_tools
from .cache_utils import get_category_stats

def tool_list(request):
    search_text = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "")
    status = request.GET.get("status", "")

    if not category_id.isdigit():
        category_id = ""

    if status not in {"active", "inactive"}:
        status = ""

    tools = (
        Tool.objects
        .select_related("category", "created_by")
        .prefetch_related("tags")
        .order_by("name", "pk")
    )

    if search_text:
        tools = tools.filter(
            Q(name__icontains=search_text)
            | Q(description__icontains=search_text)
        )

    if category_id:
        tools = tools.filter(category_id=category_id)

    if status == "active":
        tools = tools.filter(is_active=True)
    elif status == "inactive":
        tools = tools.filter(is_active=False)

    paginator = Paginator(tools, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    query_params = request.GET.copy()
    query_params.pop("page", None)

    return render(
        request,
        "rental/tool_list.html",
        {
            "tools": page_obj.object_list,
            "page_obj": page_obj,
            "categories": get_category_stats(),
            "search_text": search_text,
            "selected_category": category_id,
            "selected_status": status,
            "query_string": query_params.urlencode(),
        },
    )


@login_required(login_url="/admin/login/")
def tool_create(request):
    form = ToolForm(request.POST if request.method == "POST" else None)

    if request.method == "POST" and form.is_valid():
        tool = form.save(commit=False)
        tool.created_by = request.user
        tool.save()
        form.save_m2m()
        return redirect("rental:tool_list")

    return render(request, "rental/tool_form.html", {"form": form})


@login_required(login_url="/admin/login/")
def tool_update(request, pk):
    tool = get_object_or_404(Tool, pk=pk)
    form = ToolForm(
        request.POST if request.method == "POST" else None,
        instance=tool,
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("rental:tool_list")

    return render(
        request,
        "rental/tool_form.html",
        {"form": form, "tool": tool},
    )


@login_required(login_url="/admin/login/")
def tool_delete(request, pk):
    tool = get_object_or_404(Tool, pk=pk)

    if request.method == "POST":
        tool.delete()
        return redirect("rental:tool_list")

    return render(
        request,
        "rental/tool_confirm_delete.html",
        {"tool": tool},
    )


def availability_check(request):
    form = AvailabilityForm(request.GET or None)
    available_tools = None
    page_obj = None
    query_string = ""

    if form.is_valid():
        query_params = request.GET.copy()
        query_params.pop("page", None)
        query_string = query_params.urlencode()

        tools = get_available_tools(
            form.cleaned_data["start_date"],
            form.cleaned_data["end_date"],
        )
        paginator = Paginator(tools, 12)
        page_obj = paginator.get_page(request.GET.get("page"))
        available_tools = page_obj.object_list

    return render(
        request,
        "rental/availability.html",
        {
            "form": form,
            "available_tools": available_tools,
            "page_obj": page_obj,
            "query_string": query_string,
        },
    )
def cost_calculator(request):
    form = CostCalculatorForm(
        request.POST if request.method == "POST" else None
    )
    result = None

    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        result = calculate_rental_amounts(
            tool=data["tool"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            returned_on=data["returned_on"],
        )

    return render(
        request,
        "rental/cost_calculator.html",
        {
            "form": form,
            "result": result,
        },
    )


def demo_404(request):
    return render(request, "rental/404.html", status=404)