from django.db.models import Q

def search_medications(queryset, query):
    query = query.strip()
    if not query:
        return queryset
    return queryset.filter(Q(name__icontains=query))
