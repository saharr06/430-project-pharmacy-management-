from .services.stock import low_stock_medications


def stock_alerts(request):
    return {"stock_alert_count": low_stock_medications().count()}
