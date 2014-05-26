from models import Ngram
from rest_framework import serializers

class NgramSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Ngram
        fields = ('order', 'text', 'conditionalProbability', 'backoffWeight')
