# Django
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import ugettext as _
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse


# Codenerix
from codenerix.helpers import get_template
from codenerix.views import GenList, GenCreate, GenCreateModal, GenDetail, GenUpdate, GenUpdateModal, GenDelete, GenForeignKey

# Models
from exchange.base.models import Currency, Exchange

# Forms
from exchange.base.forms import CurrencyForm, ExchangeForm

class CurrencyList(GenList):
    model = Currency
    extra_context={'menu':['menu','currency'],'bread':[_('Menu'),_('Currency')]}

class CurrencyCreate(GenCreate):
    model = Currency
    form_class = CurrencyForm


class CurrencyCreateModal(GenCreateModal, CurrencyCreate):
    pass

class CurrencyUpdate(GenUpdate):
    model = Currency
    form_class = CurrencyForm


class CurrencyUpdateModal(GenCreateModal, CurrencyUpdate):
    pass


class CurrencyDelete(GenDelete):
    model = Currency


class CurrencyForeign(GenForeignKey):
    model = Currency
    label = '{symbol} {name} ({iso4217})'
    
    def custom_choice(self, obj, info):
        if 'buy_currency' in self.filters:
            buy = self.filters['buy_currency']
            sell = obj.pk
        elif 'sell_currency' in self.filters:
            buy = obj.pk
            sell = self.filters['sell_currency']
        else:
            buy = None
            sell = None
        
        if buy and sell:
            info['rate:__SERVICE_CALL__']=reverse('currency_online',kwargs={'sell':sell, 'buy':buy})
        
        return info
    
    def get_foreign(self, queryset, search, filters):
        return queryset.filter(
            Q(name__icontains=search) |
            Q(symbol__icontains=search) |
            Q(iso4217__icontains=search)
        )[:settings.LIMIT_FOREIGNKEY]


class CurrencyOnline(View):
    
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        # Get both values
        sell = get_object_or_404(Currency, pk=kwargs.get('sell', None))
        buy = get_object_or_404(Currency, pk=kwargs.get('buy', None))
        # Look up in the remote service
        if buy and sell:
            if buy==sell:
                rate = 1
            else:
                rate = sell.rate(buy)
        else:
            rate=None
        # Set the answer
        return JsonResponse({'value':rate})


class ExchangeList(GenList):
    model = Exchange
    show_details = True
    default_ordering = "-created"
    extra_context={'menu':['menu','exchange'],'bread':[_('Menu'),_('Exchange')]}


class ExchangeCreate(GenCreate):
    model = Exchange
    form_class = ExchangeForm


class ExchangeDetail(GenDetail):
    model = Exchange
    groups = ExchangeForm.__groups_details__()


class ExchangeUpdate(GenUpdate):
    model = Exchange
    form_class = ExchangeForm
    show_details = True


class ExchangeDelete(GenDelete):
    model = Exchange


@login_required
def not_authorized(request):
    return render(
        request,
        get_template('base/not_authorized', request.user, request.LANGUAGE_CODE)
    )


@login_required
def status(request, status, answer):
    answerjson = urlsafe_base64_decode(answer)
    status = status.lower()
    if status == 'accept':
        out = 202     # Accepted
    else:
        out = 501     # Not Implemented
    return HttpResponse(answerjson, status=out)


@login_required
def alarms(request):
    return JsonResponse({
        'body': {},
        'head': {
            'total': 0,
            'order': [],
        },
        'meta': {
            'superuser': True,
            'permitsuser': 'DC',
        }
    })


