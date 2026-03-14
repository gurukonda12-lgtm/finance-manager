from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.safestring import mark_safe
from django.views.generic.edit import FormView
from datetime import datetime
from dateutil.relativedelta import relativedelta
import plotly.express as px

from .models import Account, Liability
from .forms import LiabilityForm


def home(request):
    return render(request, 'fin_manager/home.html')


def register(request):

    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect('login')   # IMPORTANT

    else:
        form = UserCreationForm()

    return render(request, 'registration/register.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('home')


def generate_graph(data):

    fig = px.bar(data, x='months', y='expenses', title='Monthly Expenses')

    fig.update_layout(
        xaxis=dict(rangeslider=dict(visible=True)),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='rgba(0,0,0,1)',
    )

    fig.update_traces(marker_color='#008c41')

    return fig.to_json()



class ExpenseListView(LoginRequiredMixin, FormView):

    login_url = '/login/'   # if not logged in redirect to login

    template_name = 'expenses/expenses_list.html'
    form_class = LiabilityForm
    success_url = '/expenses/'

    def form_valid(self, form):

        account, _ = Account.objects.get_or_create(user=self.request.user)

        liability = Liability(
            name=form.cleaned_data['name'],
            amount=form.cleaned_data['amount'],
            interest_rate=form.cleaned_data['interest_rate'],
            date=form.cleaned_data['date'],
            end_date=form.cleaned_data['end_date'],
            long_term=form.cleaned_data['long_term'],
            user=self.request.user
        )

        liability.save()

        account.liability_list.add(liability)

        return super().form_valid(form)

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        user = self.request.user
        accounts = Account.objects.filter(user=user)

        expense_data_graph = {}
        expense_data = {}

        for account in accounts:

            liabilities = account.liability_list.all()

            for liability in liabilities:

                if liability.long_term and liability.monthly_expense:

                    current_date = liability.date

                    while current_date <= liability.end_date:

                        year_month = current_date.strftime('%Y-%m')

                        if year_month not in expense_data_graph:
                            expense_data_graph[year_month] = []

                        expense_data_graph[year_month].append({
                            'name': liability.name,
                            'amount': liability.monthly_expense,
                            'date': current_date,
                            'end_date': liability.end_date,
                        })

                        current_date = current_date + relativedelta(months=1)

                else:

                    year_month = liability.date.strftime('%Y-%m')

                    if year_month not in expense_data_graph:
                        expense_data_graph[year_month] = []

                    expense_data_graph[year_month].append({
                        'name': liability.name,
                        'amount': liability.amount,
                        'date': liability.date,
                    })

        for account in accounts:

            liabilities = account.liability_list.all()

            for liability in liabilities:

                year_month = liability.date.strftime('%Y-%m')

                if year_month not in expense_data:
                    expense_data[year_month] = []

                expense_data[year_month].append({
                    'name': liability.name,
                    'amount': liability.amount,
                    'date': liability.date,
                })

        aggregated_data = [
            {
                'year_month': key,
                'expenses': sum(item['amount'] for item in value)
            }
            for key, value in expense_data_graph.items()
        ]

        context['expense_data'] = expense_data
        context['aggregated_data'] = aggregated_data

        graph_data = {
            'months': [item['year_month'] for item in aggregated_data],
            'expenses': [item['expenses'] for item in aggregated_data]
        }

        graph_data['chart'] = generate_graph(graph_data)

        context['graph_data'] = mark_safe(graph_data['chart'])

        return context