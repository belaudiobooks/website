from rest_framework import serializers
from books import models


class PersonSimpleSerializer(serializers.ModelSerializer):
    '''
    Serializes Person to a JSON excluding certain info for usage in
    data.json export.
    '''

    class Meta:
        model = models.Person
        fields = [
            'uuid', 'name', 'description', 'description_source', 'photo',
            'photo_source', 'slug', 'gender'
        ]


class LinkSimpleSerializer(serializers.ModelSerializer):
    '''
    Serializes Link to a JSON excluding certain info for usage in
    data.json export.
    '''

    class Meta:
        model = models.Link
        fields = ['url', 'url_type']


class NarrationSimpleSerializer(serializers.ModelSerializer):
    '''
    Serializes Narration to a JSON excluding certain info for usage in
    data.json export.
    '''
    links = LinkSimpleSerializer(many=True)

    def to_representation(self, instance):
        """Convert `duration` to number of seconds."""
        ret = super().to_representation(instance)
        if instance.duration is not None:
            ret['duration'] = instance.duration_sec.total_seconds()
        return ret

    class Meta:
        model = models.Narration
        fields = ['uuid', 'narrators', 'links', 'duration']


class BookSimpleSerializer(serializers.ModelSerializer):
    '''
    Serializes Book to a JSON excluding certain info for usage in
    data.json export.
    '''
    narrations = NarrationSimpleSerializer(many=True)

    class Meta:
        model = models.Book
        fields = [
            'uuid', 'title', 'description', 'description_source', 'date',
            'authors', 'translators', 'slug', 'cover_image',
            'cover_image_source', 'tag', 'narrations'
        ]


class LinkTypeSimpleSerializer(serializers.ModelSerializer):
    '''
    Serializes LinkType to a JSON excluding certain info for usage in
    data.json export.
    '''

    class Meta:
        model = models.LinkType
        fields = ['id', 'name', 'caption', 'icon']


class TagSerializer(serializers.ModelSerializer):
    '''
    Serializes Tag to a JSON excluding certain info for usage in
    data.json export.
    '''

    class Meta:
        model = models.Tag
        fields = ['id', 'name', 'slug']