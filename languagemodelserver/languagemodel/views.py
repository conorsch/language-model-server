from django.shortcuts import render
from models import Ngram
from rest_framework import viewsets
from serializers import NgramSerializer


class NgramViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows ngrams to be viewed or edited.
    """
    queryset = Ngram.objects.all()
    serializer_class = NgramSerializer
    paginate_by = 100
